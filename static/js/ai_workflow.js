document.addEventListener('DOMContentLoaded', function() {
    const videoDetailsForm = document.getElementById('videoDetailsForm');

    // Handle form submission
    videoDetailsForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const videoData = {
            title: document.getElementById('videoTitle').value,
            category: document.getElementById('videoCategory').value,
            objective: document.getElementById('videoObjective').value,
            objectiveCategory: document.getElementById('objectiveCategory').value,
            numberOfCharacters: document.getElementById('numberOfCharacters').value
        };

        // Save the data and proceed to next step
        localStorage.setItem('videoData', JSON.stringify(videoData));
        generateScriptPrompt(videoData);
    });

    function generateScriptPrompt(videoData) {
        // Create AI prompt template
        const prompt = `Create a script for a ${videoData.category} video with the following details:

Title: ${videoData.title}
Category: ${videoData.category}
Objective: ${videoData.objective}
Objective Category: ${videoData.objectiveCategory}
Minimum total number of characters: ${videoData.numberOfCharacters}

Please generate a compelling script that:
1. Starts with a powerful hook in the first to grab attention
2. Achieves the stated objective with clear and engaging delivery
3. Is optimized for visual storytelling with dynamic pacing
4. Flows naturally and uses relatable or emotional language to connect with viewers
5. Adds at least two calls-to-action (e.g., like, comment, or subscribe) at key moments
6. Incorporates relevant keywords naturally for search optimization
7. Has a natural flow and pacing

Since I will convert this script into audio and later search for media online to compose the video, please divide the script into parts. This division will help me know when to change the media and insert a new one. Do not include any duration estimates for each part.

At the end of the script, add a section that describes how the media should be used for each part. This final section must specify that each part will have exactly one media associated with it and should provide clear guidelines on the type of media (such as an image, gif, or video clip) for each part.

***(Don't show the structure, only the text/script)*** - THIS IS VERY IMPORTANT - Of course, except for the marking, part 1, part 2, part 3, ...; As mentioned before.

Format the script with:
- Introduction
- Main content sections
- Conclusion
- Estimated duration for each section`;

        // Show script generation step
        const stepContainer = document.getElementById('step1');
        stepContainer.insertAdjacentHTML('afterend', `
            <div id="step2" class="step-container mt-4">
                <h3 class="mb-3">Step 2: Script Generation</h3>
                <div class="card bg-dark mb-3">
                    <div class="card-body">
                        <h5 class="card-title">AI Prompt</h5>
                        <div class="position-relative">
                            <textarea id="promptText" class="form-control mb-2" rows="10" readonly>${prompt}</textarea>
                            <button onclick="copyPrompt()" class="btn btn-sm btn-primary position-absolute top-0 end-0 m-2">
                                Copy Prompt
                            </button>
                        </div>
                    </div>
                </div>

                <div class="mb-3">
                    <h5>Use any of these AI platforms:</h5>
                    <div class="d-grid gap-2">
                        <a href="https://chat.openai.com" target="_blank" class="btn btn-outline-primary">ChatGPT</a>
                        <a href="https://claude.ai" target="_blank" class="btn btn-outline-primary">Claude</a>
                        <a href="https://gemini.google.com" target="_blank" class="btn btn-outline-primary">Gemini</a>
                        <a href="https://grok.xai" target="_blank" class="btn btn-outline-primary">Grok</a>
                        <a href="https://www.perplexity.ai" target="_blank" class="btn btn-outline-primary">Perplexity</a>
                        <div class="more-links" style="display: none;">
                            <a href="https://copilot.microsoft.com" target="_blank" class="btn btn-outline-primary">Copilot</a>
                            <a href="https://www.character.ai" target="_blank" class="btn btn-outline-primary">Character.AI</a>
                            <a href="https://Writesonic.com/chat" target="_blank" class="btn btn-outline-primary">Writesonic</a>
                            <a href="https://www.jasper.ai/chat" target="_blank" class="btn btn-outline-primary">Jasper</a>
                            <a href="https://www.you.com" target="_blank" class="btn btn-outline-primary">You.com</a>
                            <a href="https://poe.com" target="_blank" class="btn btn-outline-primary">Poe</a>
                            <a href="https://www.cohere.com" target="_blank" class="btn btn-outline-primary">Cohere</a>
                            <a href="https://huggingface.co/chat" target="_blank" class="btn btn-outline-primary">Hugging Chat</a>
                            <a href="https://www.meta.ai" target="_blank" class="btn btn-outline-primary">Meta AI</a>
                            <a href="https://www.chatsonic.com" target="_blank" class="btn btn-outline-primary">ChatSonic</a>
                            <a href="https://elicit.org" target="_blank" class="btn btn-outline-primary">Elicit</a>
                            <a href="https://www.anthropic.com" target="_blank" class="btn btn-outline-primary">Anthropic (General)</a>
                            <a href="https://www.pi.ai" target="_blank" class="btn btn-outline-primary">Pi</a>
                            <a href="https://www.openrouter.ai" target="_blank" class="btn btn-outline-primary">OpenRouter</a>
                            <a href="https://mistral.ai" target="_blank" class="btn btn-outline-primary">Mistral</a>
                        </div>
                        <button type="button" class="btn btn-outline-secondary btn-sm mt-2" onclick="toggleMoreLinks(this)">Mostrar mais</button>
                    </div>
                </div>

                <div class="mb-3">
                    <label for="aiResponse" class="form-label">Paste AI Response Here:</label>
                    <textarea id="aiResponse" class="form-control" rows="10" placeholder="Paste the AI-generated script here"></textarea>
                </div>

                <div class="d-grid">
                    <button onclick="proceedToTextToSpeech()" class="btn btn-primary">
                        Continue to Text-to-Speech
                    </button>
                </div>
            </div>
        `);

        // Hide step 1
        stepContainer.style.display = 'none';
    }
});

// Global functions
function copyPrompt() {
    const promptText = document.getElementById('promptText');
    promptText.select();
    document.execCommand('copy');

    // Show feedback
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    setTimeout(() => button.textContent = originalText, 2000);
}

function proceedToTextToSpeech() {
    const aiResponse = document.getElementById('aiResponse').value;
    if (!aiResponse.trim()) {
        alert('Please paste the AI-generated script before proceeding.');
        return;
    }

    // Save the script
    localStorage.setItem('videoScript', aiResponse);

    // Show text-to-speech step
    document.getElementById('step2').style.display = 'none';
    const step3Html = `
        <div id="step3" class="step-container mt-4">
            <h3 class="mb-3">Step 3: Text-to-Speech Conversion</h3>

            <div class="mb-3">
                <h5>Convert your script to speech using any of these services:</h5>
                <div class="d-grid gap-2">
                    <a href="https://elevenlabs.io" target="_blank" class="btn btn-outline-primary">ElevenLabs</a>
                    <a href="https://cloud.google.com/text-to-speech" target="_blank" class="btn btn-outline-primary">Google Cloud TTS</a>
                    <a href="https://azure.microsoft.com/en-us/services/cognitive-services/text-to-speech/" target="_blank" class="btn btn-outline-primary">Azure TTS</a>
                    <a href="https://aws.amazon.com/polly/" target="_blank" class="btn btn-outline-primary">Amazon Polly</a>
                    <a href="https://www.naturalreaders.com" target="_blank" class="btn btn-outline-primary">NaturalReaders</a>
                    <div class="more-links" style="display: none;">
                        <a href="https://www.murf.ai" target="_blank" class="btn btn-outline-primary">Murf AI</a>
                        <a href="https://www.speechify.com" target="_blank" class="btn btn-outline-primary">Speechify</a>
                        <a href="https://ttsmp3.com" target="_blank" class="btn btn-outline-primary">TTSMP3</a>
                        <a href="https://www.narakeet.com" target="_blank" class="btn btn-outline-primary">Narakeet</a>
                        <a href="https://play.ht" target="_blank" class="btn btn-outline-primary">PlayHT</a>
                        <a href="https://www.voicemod.net/text-to-speech/" target="_blank" class="btn btn-outline-primary">Voicemod TTS</a>
                        <a href="https://www.speakatoo.com" target="_blank" class="btn btn-outline-primary">Speakatoo</a>
                        <a href="https://voicemaker.in" target="_blank" class="btn btn-outline-primary">Voicemaker</a>
                        <a href="https://speechelo.com" target="_blank" class="btn btn-outline-primary">Speechelo</a>
                        <a href="https://ttsfree.com" target="_blank" class="btn btn-outline-primary">TTSFree</a>
                        <a href="https://www.media.io/text-to-speech.html" target="_blank" class="btn btn-outline-primary">Media.io TTS</a>
                        <a href="https://freetts.com" target="_blank" class="btn btn-outline-primary">FreeTTS</a>
                        <a href="https://www.lovo.ai" target="_blank" class="btn btn-outline-primary">Lovo.ai</a>
                        <a href="https://www.wideo.co/text-to-speech/" target="_blank" class="btn btn-outline-primary">Wideo TTS</a>
                        <a href="https://luvvoice.com" target="_blank" class="btn btn-outline-primary">Luvvoice</a>
                    </div>
                    <button type="button" class="btn btn-outline-secondary btn-sm mt-2" onclick="toggleMoreLinks(this)">Mostrar mais</button>
                </div>
            </div>
            <div class="mb-3">
                <label class="form-label">Upload Audio Files:</label>
                <input type="file"
                       class="form-control"
                       id="audioFile"
                       accept="audio/*"
                       multiple
                       onchange="handleAudioUpload(event)">
                <div class="form-text">(You can select multiple files at once)</div>

                <!-- Área para mostrar os arquivos selecionados -->
                <div id="selectedFiles" class="mt-2"></div>
            </div>
            <div class="d-grid">
                <button onclick="proceedToVisualContent()"
                        class="btn btn-primary"
                        disabled
                        id="visualContentBtn">
                    Continue to Visual Content
                </button>
            </div>
        </div>
    `;
    document.getElementById('step2').insertAdjacentHTML('afterend', step3Html);
}

async function handleAudioUpload(event) {
    const files = event.target.files;
    const filesPreview = document.getElementById('selectedFiles');
    filesPreview.innerHTML = '';

    if (!files || files.length === 0) return;

    try {
        // Para cada arquivo, extrair apenas a duração
        const durationEntries = await Promise.all(Array.from(files).map(file => {
            return new Promise((resolve, reject) => {
            const audio = document.createElement('audio');
            audio.src = URL.createObjectURL(file);
                audio.addEventListener('loadedmetadata', () => {
                    const duration = audio.duration;
                    URL.revokeObjectURL(audio.src);
                    resolve({ name: file.name, duration });
                });
                audio.addEventListener('error', (err) => {
                    URL.revokeObjectURL(audio.src);
                    reject(err);
                });
            });
        }));

        // Monta um dicionário: nome do arquivo → duração
        const audioDurations = {};
        durationEntries.forEach(entry => {
            audioDurations[entry.name] = entry.duration;
        });

        // Armazena o dicionário no localStorage (chave "audioDuration")
        localStorage.setItem('audioDuration', JSON.stringify(audioDurations));

        // Atualiza o preview exibindo nome e duração
        durationEntries.forEach((entry, index) => {
            filesPreview.innerHTML += `
                <div class="card mb-2">
                    <div class="card-body">
                        <h6 class="card-title">File ${index + 1}: ${entry.name}</h6>
                        <p class="card-text">
                            Duration: ${Math.round(entry.duration)} seconds
                        </p>
                    </div>
                </div>
            `;
        });

        // Habilita o botão para continuar
        document.getElementById('visualContentBtn').disabled = false;

    } catch (error) {
        console.error('Error processing audio files:', error);
        alert(`Error processing audio files: ${error.message}`);
        filesPreview.innerHTML = `
            <div class="alert alert-danger mt-2">
                Error processing files: ${error.message}
            </div>
        `;
    }
}

function proceedToVisualContent() {
    const script = localStorage.getItem('videoScript');
    const audioDurationJson = localStorage.getItem('audioDuration');

    if (!script || !audioDurationJson) {
        alert('Missing required data. Please ensure script and audio are properly loaded.');
        return;
    }

    // Recupera o dicionário com os nomes dos arquivos e suas durações
    const audioDurations = JSON.parse(audioDurationJson);

    // Cria um texto listando cada parte com o nome do arquivo e sua duração
    let audioPartsText = '';
    let partNumber = 1;
    for (const fileName in audioDurations) {
        if (audioDurations.hasOwnProperty(fileName)) {
            const duration = Math.round(audioDurations[fileName]);
            audioPartsText += `Part ${partNumber} (File: ${fileName}): ${duration} seconds\n`;
            partNumber++;
        }
    }

    // Oculta a etapa 3 (Text-to-Speech)
    document.getElementById('step3').style.display = 'none';

    // Gera o prompt para o conteúdo visual usando as durações individuais
    const visualPrompt = `Based on the following script and the durations of the individual audio segments listed below, please provide a detailed visual storyboard where each audio corresponds to one part of the script. The script is divided into parts (Part 1, Part 2, Part 3, etc.), each associated with an audio file's duration.

Audio Segments:
${audioPartsText}

Script:
${script}

###

Required Format for Each Scene:
{
    "timestamp": "0:00",
    "duration": X,
    "type": "image/gif",
    "description": "Describe what should be shown",
    "source": "Where to source this (e.g., 'Upload product photo', 'Record testimonial', 'Stock footage of city')",
    "startTransition": "one-of-available-transitions",
    "endTransition": "one-of-available-transitions",
    "filter": "one-of-available-filters"
}

Available Filters:
- grayscale: Black and white effect
- sepia: Warm brownish tone
- blur: Gaussian blur effect
- sharpen: Enhance image details
- bright: Increase brightness
- dark: Decrease brightness
- contrast: Enhance contrast
- mirror: Mirror the image
- cartoon: Cartoon-like effect
- oil_painting: Oil painting effect
- rainbow: Add rainbow overlay
- neon: Neon glow effect
- thermal: Thermal camera effect
- pencil_sketch: Pencil drawing effect
- invert: Invert colors
- emboss: Embossed texture
- glitch: Glitchy visual effect
- pixelate: Pixelation effect
- edge_detect: Highlight edges
- posterize: Reduce color levels
- solarize: Partial negative effect
- vignette: Darken edges
- halftone: Halftone print effect
- noise: Add visual noise
- color_shift: Shift color channels

Available Transitions:
Start/End transitions:
- fade-in/fade-out: Fade to/from black
- dissolve-in/dissolve-out: Gradual pixelated appearance/disappearance
- wipe-right/wipe-left: Wipe effect from right/left
- slide-right/slide-left: Slide in/out from right/left
- rotate-in/rotate-out: Rotate while appearing/disappearing
- zoom-in/zoom-out: Scale up/down effect
- blur-in/blur-out: Transition through blur
- ripple-in/ripple-out: Ripple effect transition
- spiral-in/spiral-out: Spiral pattern transition
- matrix-in/matrix-out: Digital matrix effect
- heart-in/heart-out: Heart-shaped transition
- shatter-in/shatter-out: Breaking glass effect
- glitch-in/glitch-out: Horizontal distortion glitch effect
- pixelate-in/pixelate-out: Pixelation effect while appearing/disappearing
- circle-wipe-in/circle-wipe-out: Circular wipe transition
- swirl-in/swirl-out: Swirling distortion effect
- wave-in/wave-out: Wave-like distortion transition
- tile-in/tile-out: Mosaic tile effect transition
- color-shift-in/color-shift-out: Color channel shifting effect

Please provide a complete timeline covering each part of the script with the corresponding duration as specified above. The program will use this format to automatically process the video. Please just send the format structure, nothing else added.

Example Scene:
{
    "timestamp": "0:00",
    "duration": X,
    "type": "image",
    "description": "Opening title card with company logo",
    "source": "Upload company logo image",
    "startTransition": "fade-in",
    "endTransition": "dissolve-out",
    "filter": "bright"
}
`;

    // Adiciona o HTML da etapa 4 (Visual Content) com o prompt atualizado
    const step4Html = `
        <div id="step4" class="step-container mt-4">
            <h3 class="mb-3">Step 4: Visual Content</h3>

            <div class="card bg-dark mb-3">
                <div class="card-body">
                    <h5 class="card-title">AI Prompt for Visual Content</h5>
                    <div class="position-relative">
                        <textarea id="visualPromptText" class="form-control mb-2" rows="10" readonly>${visualPrompt}</textarea>
                        <button onclick="copyVisualPrompt()" class="btn btn-sm btn-primary position-absolute top-0 end-0 m-2">
                            Copy Prompt
                        </button>
                    </div>
                </div>
            </div>

            <div class="mb-3">
                <h5>Get AI suggestions from:</h5>
                <div class="d-grid gap-2">
                    <a href="https://chat.openai.com" target="_blank" class="btn btn-outline-primary">ChatGPT</a>
                    <a href="https://claude.ai" target="_blank" class="btn btn-outline-primary">Claude</a>
                    <a href="https://gemini.google.com" target="_blank" class="btn btn-outline-primary">Gemini</a>
                    <a href="https://grok.xai" target="_blank" class="btn btn-outline-primary">Grok</a>
                    <a href="https://www.perplexity.ai" target="_blank" class="btn btn-outline-primary">Perplexity</a>
                    <div class="more-links" style="display: none;">
                        <a href="https://copilot.microsoft.com" target="_blank" class="btn btn-outline-primary">Copilot</a>
                        <a href="https://www.character.ai" target="_blank" class="btn btn-outline-primary">Character.AI</a>
                        <a href="https://writesonic.com/chat" target="_blank" class="btn btn-outline-primary">Writesonic</a>
                        <a href="https://www.jasper.ai/chat" target="_blank" class="btn btn-outline-primary">Jasper</a>
                        <a href="https://www.you.com" target="_blank" class="btn btn-outline-primary">You.com</a>
                        <a href="https://poe.com" target="_blank" class="btn btn-outline-primary">Poe</a>
                        <a href="https://www.cohere.com" target="_blank" class="btn btn-outline-primary">Cohere</a>
                        <a href="https://huggingface.co/chat" target="_blank" class="btn btn-outline-primary">Hugging Chat</a>
                        <a href="https://www.meta.ai" target="_blank" class="btn btn-outline-primary">Meta AI</a>
                        <a href="https://www.chatsonic.com" target="_blank" class="btn btn-outline-primary">ChatSonic</a>
                        <a href="https://elicit.org" target="_blank" class="btn btn-outline-primary">Elicit</a>
                        <a href="https://www.anthropic.com" target="_blank" class="btn btn-outline-primary">Anthropic (General)</a>
                        <a href="https://www.pi.ai" target="_blank" class="btn btn-outline-primary">Pi</a>
                        <a href="https://www.openrouter.ai" target="_blank" class="btn btn-outline-primary">OpenRouter</a>
                        <a href="https://mistral.ai" target="_blank" class="btn btn-outline-primary">Mistral</a>
                    </div>
                    <button type="button" class="btn btn-outline-secondary btn-sm mt-2" onclick="toggleMoreLinks(this)">Mostrar mais</button>
                </div>
            </div>

            <div class="mb-3">
                <h5>Find visual content:</h5>
                <div class="d-grid gap-2">
                    <h5>Fontes de Mídia Gratuita</h5>
                    <div class="d-grid gap-2">
                        <a href="https://unsplash.com" target="_blank" class="btn btn-outline-primary">Unsplash (Imagens Grátis)</a>
                        <a href="https://pexels.com" target="_blank" class="btn btn-outline-primary">Pexels (Imagens e Vídeos Grátis)</a>
                        <a href="https://pixabay.com" target="_blank" class="btn btn-outline-primary">Pixabay (Mídia Grátis)</a>
                        <a href="https://freepik.com" target="_blank" class="btn btn-outline-primary">Freepik (Vetores, Fotos, Ícones)</a>
                        <a href="https://stocksnap.io" target="_blank" class="btn btn-outline-primary">StockSnap (Imagens Grátis)</a>
                        <div class="more-links" style="display: none;">
                            <a href="https://burst.shopify.com" target="_blank" class="btn btn-outline-primary">Burst (Imagens de Negócios)</a>
                            <a href="https://www.videvo.net" target="_blank" class="btn btn-outline-primary">Videvo (Vídeos Grátis)</a>
                            <a href="https://coverr.co" target="_blank" class="btn btn-outline-primary">Coverr (Vídeos de Fundo)</a>
                            <a href="https://giphy.com" target="_blank" class="btn btn-outline-primary">Giphy (GIFs Grátis)</a>
                            <a href="https://tenor.com" target="_blank" class="btn btn-outline-primary">Tenor (GIFs Grátis)</a>
                        </div>
                        <button type="button" class="btn btn-outline-secondary btn-sm mt-2" onclick="toggleMoreLinks(this)">Mostrar mais</button>
                    </div>

                    <h5 class="mt-4">Ferramentas de Criação com IA</h5>
                    <div class="d-grid gap-2">
                        <a href="https://canva.com" target="_blank" class="btn btn-outline-primary">Canva (Design e Vídeo com IA)</a>
                        <a href="https://runwayml.com" target="_blank" class="btn btn-outline-primary">Runway ML (Edição de Vídeo com IA)</a>
                        <a href="https://openai.com/dall-e-2" target="_blank" class="btn btn-outline-primary">DALL·E 2 (Imagens por Texto)</a>
                        <a href="https://www.midjourney.com" target="_blank" class="btn btn-outline-primary">MidJourney (Arte com IA)</a>
                        <a href="https://www.synthesia.io" target="_blank" class="btn btn-outline-primary">Synthesia (Vídeos com Avatares)</a>
                        <div class="more-links" style="display: none;">
                            <a href="https://deepart.io" target="_blank" class="btn btn-outline-primary">DeepArt (Transformação de Imagens)</a>
                            <a href="https://www.artbreeder.com" target="_blank" class="btn btn-outline-primary">Artbreeder (Criação de Imagens)</a>
                            <a href="https://lumen5.com" target="_blank" class="btn btn-outline-primary">Lumen5 (Vídeos por Texto)</a>
                            <a href="https://pictory.ai" target="_blank" class="btn btn-outline-primary">Pictory (Vídeos por Scripts)</a>
                            <a href="https://www.descript.com" target="_blank" class="btn btn-outline-primary">Descript (Edição com IA)</a>
                        </div>
                        <button type="button" class="btn btn-outline-secondary btn-sm mt-2" onclick="toggleMoreLinks(this)">Mostrar mais</button>
                    </div>
                </div>
            </div>

            <div class="mb-3">
                <label for="aiVisualResponse" class="form-label">Paste AI Response Here:</label>
                <textarea id="aiVisualResponse" class="form-control" rows="10" placeholder="Paste the AI-generated visual timeline here"></textarea>
            </div>

            <div class="d-grid">
                <button onclick="proceedToEditor()" class="btn btn-success">
                    Continue to Video Editor
                </button>
            </div>
        </div>
    `;
    document.getElementById('step3').insertAdjacentHTML('afterend', step4Html);
}

function copyVisualPrompt() {
    const promptText = document.getElementById('visualPromptText');
    promptText.select();
    document.execCommand('copy');

    // Show feedback
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Copied!';
    setTimeout(() => button.textContent = originalText, 2000);
}

function proceedToEditor() {
    const visualResponse = document.getElementById('aiVisualResponse').value;
    if (!visualResponse.trim()) {
        alert('Please paste the AI-generated visual timeline before proceeding.');
        return;
    }

    try {
        // Debug: Log the input
        console.log('Raw visual response:', visualResponse);

        // Try to parse the response as JSON
        let timeline;
        try {
            timeline = JSON.parse(visualResponse);
            console.log('Direct JSON parse succeeded:', timeline);
        } catch (e) {
            console.log('Direct JSON parse failed, trying to extract objects');
            // If direct parsing fails, try to extract JSON objects from the text
            const jsonMatches = visualResponse.match(/\{[\s\S]*?\}/g);
            console.log('Found JSON matches:', jsonMatches);

            if (!jsonMatches) {
                throw new Error('Could not find valid JSON objects in the response');
            }
            timeline = jsonMatches.map(match => {
                try {
                    return JSON.parse(match);
                } catch (err) {
                    console.error('Failed to parse timeline item:', match);
                    return null;
                }
            }).filter(item => item !== null);

            if (timeline.length === 0) {
                throw new Error('No valid timeline items found');
            }
            console.log('Extracted timeline:', timeline);
        }

        // Validate the timeline structure
        if (!Array.isArray(timeline)) {
            timeline = [timeline]; // Convert single object to array
        }

        // Validate each timeline item
        timeline = timeline.map(item => ({
            timestamp: item.timestamp || "0:00",
            duration: parseFloat(item.duration) || 5,
            type: item.type || "image",
            description: item.description || "",
            source: item.source || "",
            startTransition: item.startTransition || "fade-in",
            endTransition: item.endTransition || "fade-out",
            filter: item.filter || "none"
        }));

        console.log('Final validated timeline:', timeline);

        // Sort timeline by timestamp
        timeline.sort((a, b) => {
            const timeA = a.timestamp.split(':').map(Number);
            const timeB = b.timestamp.split(':').map(Number);
            return (timeA[0] * 60 + timeA[1]) - (timeB[0] * 60 + timeB[1]);
        });

        // Save the validated and formatted timeline
        localStorage.setItem('visualTimeline', JSON.stringify(timeline));
        console.log('Saved to localStorage:', localStorage.getItem('visualTimeline'));

        // Add a delay before redirecting and show success message
        alert('Timeline processed successfully! Redirecting to editor...');
        setTimeout(() => {
            window.location.href = '/editor';
        }, 2000); // 2 second delay to see console logs

    } catch (error) {
        console.error('Error processing timeline:', error);
        // Show error in alert and don't redirect
        alert('Error processing the visual timeline: ' + error.message + '\nPlease ensure it follows the exact format shown in the prompt and try again.');
    }
}

// New global function to toggle the visibility of extra links
function toggleMoreLinks(btn) {
    const moreLinksDiv = btn.previousElementSibling;
    if (moreLinksDiv && moreLinksDiv.classList.contains('more-links')) {
        if (moreLinksDiv.style.display === 'none') {
            moreLinksDiv.style.display = 'block';
            btn.textContent = 'Mostrar menos';
        } else {
            moreLinksDiv.style.display = 'none';
            btn.textContent = 'Mostrar mais';
        }
    }
}
