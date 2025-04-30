/**
 * A class that parses chat messages and does things like add emotes, etc.
 * 
 * @class ChatMessageParser
 * @property {Object} emotes - A dictionary of emotes, where the key is the emote name, and the value is an object with
 *      the following properties:
 *          - `urls` - An object of urls for the emote, where the key is the size multiplier of the emote, and the
 *             value is the url to the emote.
 *          - `id` - The id of the emote.
 *          - `source` - The source of the emote. (e.g. "twitch", "bttv", "7tv", "ffz")
 *
 * @example
 * let parser = new ChatMessageParser();
 * 
 * // Use async/await
 * await parser.load();
 * 
 * // Or use .then()
 * parser.load().then(() => {
 *    // Now the emotes are loaded.
 * });
 * 
 * // Later:
 * let message = parser.parseUnsafe("Hello, Kappa!");
 * console.log(message); // Hello, <img src="https://static-cdn.jtvnw.net/emoticons/v1/25/1.0" class="twitch-emote" />!
 *  
 */
class ChatMessageParser
{
    emotes = {};

    /**
     * Loads external data, i.e. emote map. (Can be extended to load other data required for parsing messages in the 
     * future.)
     * 
     * @returns {Promise<void>} A promise that resolves when the data are loaded.
     */
    async load()
    {
        // Load Emotes
        let response = await fetch("emotes.json");
        this.emotes = await response.json();

        // Other data can be loaded here.
    }

    /**
     * Parses a chat message and do things like replaces emotes with html elements. This version returns an <li> 
     * element with the message inside, along with <img> and <span> elements. This function should be considered safe 
     * against XSS attacks.
     * 
     * @param {string} message - The message to parse.
     * 
     * @returns {HTMLLIElement} An <span> element with the message parsed into html elements.
     */
    parseSafe(message)
    {
        // Twitch Emotes are simply just a word burried in the message. We need to split the message into words and try a lookup for each word. If one is found, we replace it with an image, otherwise we just leave it as is.
        let words = message.split(" ");
        let parsedMessage = document.createElement("span");

        for (let i = 0; i < words.length; i++)
        {
            let word = words[i];
            // Strip out any punctuation from the word.
            word = word.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g,"");
            let emote = this.emotes[word];

            if(emote)
            {
                let image = document.createElement("img");
                image.src = emote.urls["url_2x"];
                image.width = "28";
                image.classList.add("twitch-emote");
                parsedMessage.appendChild(image);
            }
            else
            {
                parsedMessage.appendChild(document.createTextNode(word));
            }

            if(i < words.length - 1)
            {
                parsedMessage.appendChild(document.createTextNode(" "));
            }
        }

        return parsedMessage;
    }
}

// Since we're not using a bundler, we need to manually export the class.
window.ChatMessageParser = ChatMessageParser;