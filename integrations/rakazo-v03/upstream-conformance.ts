/** Run in the actual Rakazo checkout with its own locked TypeScript/dependencies. */
import type {SandboxProvider} from '../../packages/adapter-kit/src/interfaces.js';
import {createSandboxProvider} from '../../packages/adapters/src/sandbox-factory.js';
import type {Provider} from './service.js';
const upstream: SandboxProvider = createSandboxProvider('docker',{});
const compatible: Provider = upstream;
void compatible; // Compile-time contract only; do not execute this as a provisioning script.
