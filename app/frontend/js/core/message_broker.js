export default class MessageBroker {
    constructor() {
        this.registry = new Map();
    }

    /**
     * Strictly registers a module and its public message handlers.
     * @param {string} moduleName - The unique identifier for the module.
     * @param {Object} handlers - A dictionary mapping action strings to functions.
     */
    register(moduleName, handlers) {
        if (this.registry.has(moduleName)) {
            throw new Error(`[MessageBroker] Fatal: Module '${moduleName}' is already registered.`);
        }
        this.registry.set(moduleName, handlers);
        // Optional: Leave this in during development for perfect traceability
        // console.log(`[MessageBroker] Registered: ${moduleName}`); 
    }

    /**
     * Routes a message directly to a specific module.
     * @param {string} targetModule - The registered name of the receiving module.
     * @param {string} action - The specific action the target should execute.
     * @param {any} payload - Optional data payload.
     */
    send(targetModule, action, payload = null) {
        const handlers = this.registry.get(targetModule);
        
        if (!handlers) {
            throw new Error(`[MessageBroker] Fault: Attempted to send message to unregistered module '${targetModule}'.`);
        }
        
        if (typeof handlers[action] !== 'function') {
            throw new Error(`[MessageBroker] Fault: Module '${targetModule}' does not support action '${action}'.`);
        }

        // Execute the targeted action. 
        // Returning the result allows for synchronous two-way communication if needed.
        return handlers[action](payload); 
    }
}