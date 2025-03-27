const knex = require('knex');

class DatabaseConnection {
    constructor(config) {
        this.config = config;
        this.knexInstance = null;
        this.isConnected = false;
        this.retryAttempts = 3;
        this.retryDelay = 5000; // 5 seconds
    }

    async connect() {
        try {
            // Validate config
            this._validateConfig();

            console.log('Attempting to connect to database with config:', {
                host: this.config.connection.host,
                port: this.config.connection.port,
                database: this.config.connection.database,
                user: this.config.connection.user,
                pool: this.config.pool
            });

            // Initialize knex with pool
            this.knexInstance = knex(this.config);

            // Test connection
            await this.knexInstance.raw('SELECT 1');
            this.isConnected = true;
            console.log('Database connected successfully');
            return true;

        } catch (error) {
            console.error('Database connection error:', {
                message: error.message,
                code: error.code,
                stack: error.stack,
                config: {
                    host: this.config.connection.host,
                    port: this.config.connection.port,
                    database: this.config.connection.database,
                    user: this.config.connection.user
                }
            });
            
            if (this.retryAttempts > 0) {
                this.retryAttempts--;
                console.log(`Retrying connection in ${this.retryDelay/1000}s... (Attempts left: ${this.retryAttempts})`);
                await new Promise(resolve => setTimeout(resolve, this.retryDelay));
                return this.connect();
            }
            
            throw new Error('Failed to connect to database after multiple attempts');
        }
    }

    _validateConfig() {
        const required = ['host', 'port', 'database'];
        for (const field of required) {
            if (!this.config.connection[field]) {
                throw new Error(`Missing required config field: ${field}`);
            }
        }
    }

    async disconnect() {
        try {
            if (this.knexInstance) {
                await this.knexInstance.destroy();
            }
            this.isConnected = false;
            console.log('Database disconnected successfully');
        } catch (error) {
            console.error('Error disconnecting from database:', error);
            throw error;
        }
    }

    getKnex() {
        if (!this.isConnected) {
            throw new Error('Database not connected');
        }
        return this.knexInstance;
    }

    async healthCheck() {
        try {
            if (!this.isConnected) {
                await this.connect();
            }
            await this.knexInstance.raw('SELECT 1');
            return { status: 'connected' };
        } catch (error) {
            this.isConnected = false;
            return { 
                status: 'error',
                message: error.message
            };
        }
    }
}

module.exports = DatabaseConnection;
