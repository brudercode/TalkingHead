/**
 * Taurus ArchCard SDK
 * Integrates TalkingHead library with EcoChiefs Oracle interface
 */

import { TalkingHead } from '../../../modules/talkinghead.mjs';

export class TaurusAvatarStage {
    constructor(canvasId, options = {}) {
        this.canvasId = canvasId;
        this.head = null;
        this.isReady = false;

        // Default configuration
        this.config = {
            ttsEndpoint: null,
            ttsVoice: 'en-US-Neural2-J', // Deep, authoritative voice for Taurus
            avatarMood: 'neutral',
            cameraView: 'full',
            ...options
        };

        // Asset paths - loaded from registry via card_bindings
        this.assetPaths = {
            model: options.modelPath || '/assets/taurus/taurus-meshy-v1.glb',
            background: options.backgroundPath || null,
        };
    }

    /**
     * Initialize TalkingHead and load Taurus avatar
     */
    async init() {
        try {
            // Create TalkingHead instance
            this.head = new TalkingHead(this.canvasId, {
                ttsEndpoint: this.config.ttsEndpoint,
                ttsVoice: this.config.ttsVoice,
                cameraView: this.config.cameraView,
                avatarMood: this.config.avatarMood,
                lipsyncLang: 'en'
            });

            // Wait for TalkingHead to be ready
            await this.head.showAvatar({
                url: this.assetPaths.model,
                body: 'M',
                avatarMood: this.config.avatarMood,
                ttsVoice: this.config.ttsVoice,
                lipsyncLang: 'en'
            });

            this.isReady = true;
            console.log('✅ Taurus Avatar Stage initialized');

            return this;
        } catch (error) {
            console.error('❌ Failed to initialize Taurus Avatar:', error);
            throw error;
        }
    }

    /**
     * Make Taurus speak oracle wisdom
     * @param {string} text - Text to speak
     * @param {Object} options - Speaking options
     */
    async speak(text, options = {}) {
        if (!this.isReady) {
            throw new Error('TaurusAvatarStage not initialized. Call init() first.');
        }

        const speakOptions = {
            text,
            ...options
        };

        await this.head.speakText(speakOptions);
    }

    /**
     * Stream oracle response (for real-time TTS)
     * @param {Object} options - Streaming options
     */
    async startStream(options = {}) {
        if (!this.isReady) {
            throw new Error('TaurusAvatarStage not initialized. Call init() first.');
        }

        return await this.head.streamStart(options);
    }

    /**
     * Stream audio chunk
     */
    async streamAudio(chunk) {
        return await this.head.streamAudio(chunk);
    }

    /**
     * End streaming session
     */
    async endStream() {
        return await this.head.streamNotifyEnd();
    }

    /**
     * Interrupt current speech
     */
    async interrupt() {
        return await this.head.streamInterrupt();
    }

    /**
     * Change Taurus mood/expression
     * @param {string} mood - Mood name (neutral, happy, sad, angry, etc.)
     */
    setMood(mood) {
        if (!this.isReady) return;
        this.head.setMood(mood);
    }

    /**
     * Play gesture/animation
     * @param {string} gesture - Gesture name
     */
    playGesture(gesture) {
        if (!this.isReady) return;
        this.head.playGesture(gesture);
    }

    /**
     * Set camera view
     * @param {string} view - View name (full, mid, upper, head)
     */
    setView(view) {
        if (!this.isReady) return;
        this.head.setView(view);
    }

    /**
     * Make Taurus look at camera (engage user)
     */
    lookAtCamera(duration = 1000) {
        if (!this.isReady) return;
        this.head.lookAtCamera(duration);
    }

    /**
     * Consult oracle - main interaction method
     * @param {string} question - User's question
     * @param {Function} onResponse - Callback with oracle response
     */
    async consultOracle(question, onResponse) {
        if (!this.isReady) {
            throw new Error('TaurusAvatarStage not initialized. Call init() first.');
        }

        // Look at camera to engage user
        this.lookAtCamera();

        // Oracle thinking gesture
        this.playGesture('thoughtful');

        // Get oracle response (placeholder - integrate with your oracle backend)
        const response = await this.getOracleResponse(question);

        // Deliver wisdom
        if (onResponse) {
            onResponse(response);
        }

        await this.speak(response.text, {
            onSubtitles: (text) => {
                // Update subtitles in UI
                this.updateSubtitles(text);
            }
        });

        return response;
    }

    /**
     * Get oracle response from backend
     * @param {string} question
     * @private
     */
    async getOracleResponse(question) {
        // TODO: Integrate with your oracle backend/LLM
        // For now, return placeholder wisdom
        return {
            text: "As Taurus, Chief Guardian of Value and Stewardship, I counsel patience and mindful resource allocation. Every decision ripples through the Terra Ledger.",
            guidance: "balance",
            scrollUpdate: {
                assetsOfPurpose: "+2",
                balanceOfImpact: "→",
                legacyOfProsperity: "+1"
            }
        };
    }

    /**
     * Update subtitles in UI
     * @param {string} text
     * @private
     */
    updateSubtitles(text) {
        const subtitleElement = document.getElementById('oracle-subtitles');
        if (subtitleElement) {
            subtitleElement.textContent = text;
        }
    }

    /**
     * Dispose and cleanup
     */
    dispose() {
        if (this.head) {
            this.head.dispose();
            this.head = null;
        }
        this.isReady = false;
    }
}

/**
 * Helper to load model from registry
 * @param {string} identityId - e.g., 'ecochief.taurus'
 * @param {string} slot - e.g., 'avatar3d'
 * @returns {string} - Model path
 */
export async function getModelFromRegistry(identityId, slot = 'avatar3d') {
    // TODO: Query registry API or read from card_bindings
    // For now, use convention-based path
    const identity = identityId.split('.').pop(); // 'taurus'
    return `/assets/${identity}/${identity}-${slot}.glb`;
}
