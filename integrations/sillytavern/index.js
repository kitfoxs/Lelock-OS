import { getContext, extension_settings, renderExtensionTemplateAsync } from '../../extensions.js';
import { eventSource, event_types, setExtensionPrompt, extension_prompt_roles, saveSettingsDebounced } from '../../../script.js';
import { ToolManager } from '../../tool-calling.js';
import { SlashCommandParser } from '../../slash-commands/SlashCommandParser.js';
import { SlashCommand } from '../../slash-commands/SlashCommand.js';
import { SlashCommandArgument, SlashCommandNamedArgument, ARGUMENT_TYPE } from '../../slash-commands/SlashCommandArgument.js';
import { Popup } from '../../popup.js';

export { MODULE_NAME };

const MODULE_NAME = 'lelock_os';
const DEFAULT_DAEMON_URL = 'http://127.0.0.1:8780';

const defaultSettings = {
    daemon_url: DEFAULT_DAEMON_URL,
    auto_recall: true,
    recall_limit: 3,
    enable_tools: true,
    seed_lore: true,
};

let isConnected = false;
let daemonStatus = null;

// ============================================================================
// API Client
// ============================================================================

function getDaemonUrl() {
    return extension_settings[MODULE_NAME]?.daemon_url || DEFAULT_DAEMON_URL;
}

async function apiCall(endpoint, method = 'GET', body = null) {
    const base = getDaemonUrl().replace(/\/+$/, '');
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body && method !== 'GET') {
        options.body = JSON.stringify(body);
    }
    const resp = await fetch(`${base}${endpoint}`, options);
    if (!resp.ok) {
        let err = `HTTP ${resp.status}`;
        try {
            const j = await resp.json();
            if (j.error) err = j.error;
        } catch (_) {}
        throw new Error(err);
    }
    return await resp.json();
}

// ============================================================================
// Connection Status Check
// ============================================================================

async function checkConnection() {
    const badge = $('#lelock_connection_badge');
    try {
        const data = await apiCall('/status');
        isConnected = true;
        daemonStatus = data;
        badge.removeClass('disconnected').addClass('connected').text(`Connected (${data.companion})`);
        $('#lelock_companion_name').text(data.companion || 'Unknown');
        $('#lelock_scope_val').text(data.scope || 'personal');
        $('#lelock_workspace_val').text(data.workspace || '—');
        $('#lelock_wing_val').text(data.palace_wing || '—');
    } catch (err) {
        isConnected = false;
        daemonStatus = null;
        badge.removeClass('connected').addClass('disconnected').text('Disconnected');
        $('#lelock_companion_name').text('—');
        $('#lelock_scope_val').text('—');
        $('#lelock_workspace_val').text('—');
        $('#lelock_wing_val').text('—');
    }
}

// ============================================================================
// MemPalace Autonomous Recall (Context Injection)
// ============================================================================

async function onBeforeCombinePrompts() {
    const settings = extension_settings[MODULE_NAME];
    if (!settings?.auto_recall || !isConnected) {
        setExtensionPrompt('lelock_palace', '', 1, 2);
        return;
    }

    try {
        const context = getContext();
        const chat = context.chat || [];
        if (chat.length === 0) return;

        // Take the latest user message or conversation snippet as semantic query
        const lastUserMessage = [...chat].reverse().find(m => m.is_user && !m.is_system);
        if (!lastUserMessage || !lastUserMessage.mes) return;

        const query = lastUserMessage.mes.slice(0, 200);
        const limit = Number(settings.recall_limit || 3);
        const result = await apiCall('/api/recall', 'POST', { query, limit });

        if (result.ok && result.memories && result.memories.length > 0) {
            const memoryLines = result.memories.map(m => `* ${m.content}`).join('\n');
            const injection = `[Relevant memories and facts from MemPalace for this conversation:\n${memoryLines}\nEnd of recalled memories.]`;
            // Inject at depth 2 (above the immediate latest exchange)
            setExtensionPrompt('lelock_palace', injection, 1, 2, false, extension_prompt_roles.SYSTEM);
        } else {
            setExtensionPrompt('lelock_palace', '', 1, 2);
        }
    } catch (err) {
        console.warn('[Lelock OS] Auto-recall error:', err);
        setExtensionPrompt('lelock_palace', '', 1, 2);
    }
}

// ============================================================================
// In-Chat Interactive Proposal Cards
// ============================================================================

function renderProposalWidget(messageElement, proposal, messageId) {
    if (messageElement.find(`.lelock-proposal-box[data-prop-id="${proposal.id}"]`).length > 0) {
        return;
    }

    const payload = proposal.payload || {};
    const path = payload.path || 'workspace/unnamed.txt';
    const content = payload.content || '';
    const state = proposal.state || 'pending';

    const box = $(`
        <div class="lelock-proposal-box" data-prop-id="${proposal.id}">
            <div class="lelock-proposal-header">
                <span class="lelock-proposal-title">
                    <i class="fa-solid fa-file-code"></i> Workspace Proposal
                </span>
                <span class="lelock-proposal-path">${escapeHtml(path)}</span>
            </div>
            <div class="lelock-proposal-diff-toggle">Toggle Content Preview (${content.length} chars)</div>
            <pre class="lelock-proposal-content displayNone">${escapeHtml(content)}</pre>
            <div class="lelock-proposal-actions">
                ${state === 'pending' ? `
                    <button class="lelock-btn-approve"><i class="fa-solid fa-check"></i> Approve & Write</button>
                    <button class="lelock-btn-reject"><i class="fa-solid fa-xmark"></i> Reject</button>
                ` : `
                    <span class="lelock-proposal-status-pill ${state}">${state.toUpperCase()}</span>
                `}
            </div>
        </div>
    `);

    box.find('.lelock-proposal-diff-toggle').on('click', function () {
        box.find('.lelock-proposal-content').slideToggle(150);
    });

    box.find('.lelock-btn-approve').on('click', async function () {
        const btn = $(this);
        btn.prop('disabled', true).text('Applying...');
        try {
            const res = await apiCall('/api/proposals/approve', 'POST', { id: proposal.id });
            box.find('.lelock-proposal-actions').html('<span class="lelock-proposal-status-pill approved">APPROVED & WRITTEN</span>');
            toastr.success(`File written to workspace: ${path}`);
        } catch (err) {
            btn.prop('disabled', false).text('Approve & Write');
            toastr.error(`Approval failed: ${err.message}`);
        }
    });

    box.find('.lelock-btn-reject').on('click', async function () {
        try {
            await apiCall('/api/proposals/reject', 'POST', { id: proposal.id });
            box.find('.lelock-proposal-actions').html('<span class="lelock-proposal-status-pill rejected">REJECTED</span>');
            toastr.info(`Proposal ${proposal.id} rejected.`);
        } catch (err) {
            toastr.error(`Rejection failed: ${err.message}`);
        }
    });

    messageElement.find('.mes_text').append(box);
}

async function onCharacterMessageRendered(messageId) {
    if (!isConnected) return;
    const context = getContext();
    const chat = context.chat || [];
    const message = chat[messageId];
    if (!message || message.is_user) return;

    const messageElement = $(`.mes[mesid="${messageId}"]`);
    if (!messageElement.length) return;

    // Check if message contains proposal tag or extra metadata
    if (message.extra?.lelock_proposal) {
        renderProposalWidget(messageElement, message.extra.lelock_proposal, messageId);
        return;
    }

    // Check for pending proposals in the daemon created in this turn
    try {
        const pend = await apiCall('/api/proposals/pending');
        if (pend.ok && pend.proposals && pend.proposals.length > 0) {
            const latest = pend.proposals[pend.proposals.length - 1];
            // If the latest message mentions the proposal path or file
            const payload = latest.payload || {};
            if (payload.path && message.mes && message.mes.includes(payload.path)) {
                message.extra = message.extra || {};
                message.extra.lelock_proposal = latest;
                renderProposalWidget(messageElement, latest, messageId);
                await context.saveChat();
            }
        }
    } catch (_) {}
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ============================================================================
// ToolManager Function Tools
// ============================================================================

function registerLelockTools() {
    if (typeof ToolManager === 'undefined' || !ToolManager.registerFunctionTool) {
        console.warn('[Lelock OS] SillyTavern ToolManager not found; skipping tool registration.');
        return;
    }

    // 1. Read Workspace File
    ToolManager.registerFunctionTool({
        name: 'lelock_read_text',
        displayName: 'Lelock Read Workspace File',
        description: 'Read a regular text file from the authorized local workspace. Only non-symlinked UTF-8 text files are permitted.',
        parameters: {
            type: 'object',
            properties: {
                path: {
                    type: 'string',
                    description: 'Relative path within the workspace (e.g. "src/main.py"). No absolute paths or traversal.',
                },
            },
            required: ['path'],
        },
        action: async (args) => {
            try {
                const res = await apiCall('/api/read-file', 'POST', { path: args.path });
                return JSON.stringify(res.file);
            } catch (err) {
                return JSON.stringify({ ok: false, error: err.message });
            }
        },
    });

    // 2. Propose Write to Workspace
    ToolManager.registerFunctionTool({
        name: 'lelock_write_text',
        displayName: 'Lelock Propose File Write',
        description: 'Propose creating or updating a file in the workspace. All writes are proposals requiring human confirmation before committing to disk.',
        parameters: {
            type: 'object',
            properties: {
                path: {
                    type: 'string',
                    description: 'Relative path for the file to create in workspace (e.g. "src/agent.py").',
                },
                content: {
                    type: 'string',
                    description: 'Full UTF-8 content of the proposed file.',
                },
            },
            required: ['path', 'content'],
        },
        action: async (args) => {
            try {
                const res = await apiCall('/api/proposals/create', 'POST', {
                    action: 'write',
                    path: args.path,
                    content: args.content,
                });
                return JSON.stringify({
                    status: 'pending_human_approval',
                    proposal_id: res.proposal.proposal_id,
                    notice: 'Your proposed file write has been staged. It will be committed to disk as soon as the operator clicks Approve in the chat.',
                });
            } catch (err) {
                return JSON.stringify({ ok: false, error: err.message });
            }
        },
    });

    // 3. Recall from MemPalace
    ToolManager.registerFunctionTool({
        name: 'lelock_recall',
        displayName: 'Lelock Recall Memory',
        description: 'Search your MemPalace memory repository for factual historical records and past user preferences.',
        parameters: {
            type: 'object',
            properties: {
                query: {
                    type: 'string',
                    description: 'Search query for long-term memory retrieval.',
                },
                limit: {
                    type: 'integer',
                    description: 'Maximum number of memory drawers to retrieve (default: 5).',
                },
            },
            required: ['query'],
        },
        action: async (args) => {
            try {
                const res = await apiCall('/api/recall', 'POST', { query: args.query, limit: args.limit || 5 });
                return JSON.stringify(res);
            } catch (err) {
                return JSON.stringify({ ok: false, error: err.message });
            }
        },
    });

    // 4. Remember into MemPalace
    ToolManager.registerFunctionTool({
        name: 'lelock_remember',
        displayName: 'Lelock Remember Fact',
        description: 'Permanently store a new fact, project detail, or user preference into your local MemPalace.',
        parameters: {
            type: 'object',
            properties: {
                content: {
                    type: 'string',
                    description: 'Factual text to store permanently.',
                },
                kind: {
                    type: 'string',
                    enum: ['fact', 'preference', 'project', 'episode', 'fiction'],
                    description: 'Category of memory.',
                },
            },
            required: ['content'],
        },
        action: async (args) => {
            try {
                const res = await apiCall('/api/remember', 'POST', {
                    content: args.content,
                    kind: args.kind || 'fact',
                });
                return JSON.stringify(res);
            } catch (err) {
                return JSON.stringify({ ok: false, error: err.message });
            }
        },
    });

    // 5. Check System Status
    ToolManager.registerFunctionTool({
        name: 'lelock_status',
        displayName: 'Lelock System Status',
        description: 'Check active companion identity, authorized workspace path, and MemPalace connection.',
        parameters: {
            type: 'object',
            properties: {},
        },
        action: async () => {
            try {
                const res = await apiCall('/status');
                return JSON.stringify(res);
            } catch (err) {
                return JSON.stringify({ ok: false, error: err.message });
            }
        },
    });

    console.log('[Lelock OS] Registered 5 workspace and memory tools with ToolManager.');
}

// ============================================================================
// Character Card & Lorebook Sync
// ============================================================================

async function syncActiveCharacter() {
    const context = getContext();
    const charId = context.characterId;
    if (charId === undefined || charId === null || !context.characters || !context.characters[charId]) {
        toastr.warning('Please select an active character in SillyTavern first.');
        return;
    }

    const char = context.characters[charId];
    const feedback = $('#lelock_sync_feedback');
    feedback.removeClass('displayNone success error').text('Syncing character and lorebook to Lelock OS...');

    try {
        const seedLore = $('#lelock_seed_lore_checkbox').is(':checked');
        const res = await apiCall('/api/sync-card', 'POST', {
            card: char,
            seed_lore: seedLore,
        });

        if (res.ok) {
            feedback.addClass('success').text(`Successfully synced ${res.companion}! Seeded ${res.lore_seeded_count} lorebook entries into MemPalace.`);
            toastr.success(`Synced ${res.companion} with Lelock OS.`);
            await checkConnection();
        } else {
            feedback.addClass('error').text(`Sync failed: ${res.error || 'Unknown error'}`);
        }
    } catch (err) {
        feedback.addClass('error').text(`Sync failed: ${err.message}`);
        toastr.error(`Sync failed: ${err.message}`);
    }
}

// ============================================================================
// Slash Commands
// ============================================================================

function registerSlashCommands() {
    SlashCommandParser.addCommandObject(SlashCommand.fromProps({
        name: 'lelock-status',
        callback: async () => {
            try {
                const status = await apiCall('/status');
                return JSON.stringify(status, null, 2);
            } catch (err) {
                return `Lelock Error: ${err.message}`;
            }
        },
        helpString: 'Inspect Lelock OS bridge connection, workspace path, and MemPalace health.',
    }));

    SlashCommandParser.addCommandObject(SlashCommand.fromProps({
        name: 'lelock-recall',
        callback: async (namedArgs, unnamedArgs) => {
            const query = unnamedArgs.trim();
            if (!query) return 'Usage: /lelock-recall <query>';
            try {
                const res = await apiCall('/api/recall', 'POST', { query, limit: 5 });
                if (!res.memories || res.memories.length === 0) return 'No matching memories found in MemPalace.';
                return res.memories.map(m => `[${m.kind}] ${m.content}`).join('\n\n');
            } catch (err) {
                return `Recall failed: ${err.message}`;
            }
        },
        helpString: 'Query the Lelock MemPalace memory repository.',
    }));

    SlashCommandParser.addCommandObject(SlashCommand.fromProps({
        name: 'lelock-remember',
        callback: async (namedArgs, unnamedArgs) => {
            const content = unnamedArgs.trim();
            if (!content) return 'Usage: /lelock-remember <fact to save>';
            try {
                const res = await apiCall('/api/remember', 'POST', { content, kind: 'fact' });
                return `Saved memory to MemPalace (drawer: ${res.drawer_id})`;
            } catch (err) {
                return `Remember failed: ${err.message}`;
            }
        },
        helpString: 'Save a permanent fact or preference directly into MemPalace.',
    }));

    SlashCommandParser.addCommandObject(SlashCommand.fromProps({
        name: 'lelock-sync',
        callback: async () => {
            await syncActiveCharacter();
            return 'Character sync initiated.';
        },
        helpString: 'Sync the currently loaded character card and lorebook to Lelock OS.',
    }));
}

// ============================================================================
// UI Setup & Listeners
// ============================================================================

function setupSettingsListeners() {
    $('#lelock_btn_refresh').off('click').on('click', async () => {
        await checkConnection();
    });

    $('#lelock_daemon_url').off('change').on('change', function () {
        extension_settings[MODULE_NAME].daemon_url = $(this).val().trim();
        saveSettingsDebounced();
        checkConnection();
    });

    $('#lelock_auto_recall').off('change').on('change', function () {
        extension_settings[MODULE_NAME].auto_recall = $(this).is(':checked');
        saveSettingsDebounced();
    });

    $('#lelock_recall_limit').off('input').on('input', function () {
        const val = $(this).val();
        $('#lelock_recall_limit_val').text(val);
        extension_settings[MODULE_NAME].recall_limit = Number(val);
        saveSettingsDebounced();
    });

    $('#lelock_enable_tools').off('change').on('change', function () {
        extension_settings[MODULE_NAME].enable_tools = $(this).is(':checked');
        saveSettingsDebounced();
    });

    $('#lelock_seed_lore_checkbox').off('change').on('change', function () {
        extension_settings[MODULE_NAME].seed_lore = $(this).is(':checked');
        saveSettingsDebounced();
    });

    $('#lelock_btn_sync_card').off('click').on('click', async () => {
        await syncActiveCharacter();
    });

    $('#lelock_btn_view_pending').off('click').on('click', async () => {
        try {
            const res = await apiCall('/api/proposals/pending');
            const props = res.proposals || [];
            if (props.length === 0) {
                toastr.info('No pending workspace proposals.');
                return;
            }
            const list = props.map(p => `ID: ${p.id} | Kind: ${p.kind} | Path: ${p.payload?.path || 'n/a'}`).join('\n');
            alert(`Pending Proposals (${props.length}):\n\n${list}`);
        } catch (err) {
            toastr.error(`Could not fetch proposals: ${err.message}`);
        }
    });
}

// ============================================================================
// Extension Lifecycle Initialization
// ============================================================================

export async function init() {
    console.log('[Lelock OS] Initializing SillyTavern Extension...');

    // 1. Initialize settings
    extension_settings[MODULE_NAME] = Object.assign({}, defaultSettings, extension_settings[MODULE_NAME] || {});

    // 2. Render Settings HTML
    const settingsHtml = await renderExtensionTemplateAsync('third-party/lelock-os', 'settings');
    $('#extensions_settings').append(settingsHtml);

    // Apply values to UI
    $('#lelock_daemon_url').val(extension_settings[MODULE_NAME].daemon_url);
    $('#lelock_auto_recall').prop('checked', extension_settings[MODULE_NAME].auto_recall);
    $('#lelock_recall_limit').val(extension_settings[MODULE_NAME].recall_limit);
    $('#lelock_recall_limit_val').text(extension_settings[MODULE_NAME].recall_limit);
    $('#lelock_enable_tools').prop('checked', extension_settings[MODULE_NAME].enable_tools);
    $('#lelock_seed_lore_checkbox').prop('checked', extension_settings[MODULE_NAME].seed_lore);

    setupSettingsListeners();

    // 3. Register Function Tools & Slash Commands
    if (extension_settings[MODULE_NAME].enable_tools) {
        registerLelockTools();
    }
    registerSlashCommands();

    // 4. Hook Event Listeners
    eventSource.on(event_types.GENERATE_BEFORE_COMBINE_PROMPTS, onBeforeCombinePrompts);
    eventSource.on(event_types.CHARACTER_MESSAGE_RENDERED, onCharacterMessageRendered);
    eventSource.on(event_types.CHAT_CHANGED, () => {
        setExtensionPrompt('lelock_palace', '', 1, 2);
    });

    // 5. Initial connection ping
    await checkConnection();
    console.log('[Lelock OS] Extension initialization complete.');
}
