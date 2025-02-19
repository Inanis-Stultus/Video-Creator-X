document.addEventListener('DOMContentLoaded', function() {
    const videoDetailsForm = document.getElementById('videoDetailsForm');

    // Handle form submission
    videoDetailsForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const videoData = {
            title: document.getElementById('videoTitle').value,
            category: document.getElementById('videoCategory').value,
            objective: document.getElementById('videoObjective').value,
            objectiveCategory: document.getElementById('objectiveCategory').value
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

Please generate a compelling script that:
1. Achieves the stated objective
2. Is engaging and well-structured
3. Is optimized for visual storytelling
4. Includes clear scene descriptions and transitions
5. Has a natural flow and pacing

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
                        <a href="https://bard.google.com" target="_blank" class="btn btn-outline-primary">Bard</a>
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
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label">Upload Audio File:</label>
                <input type="file" class="form-control" id="audioFile" accept="audio/*" onchange="handleAudioUpload(event)">
            </div>

            <div class="d-grid">
                <button onclick="proceedToVisualContent()" class="btn btn-primary" disabled id="visualContentBtn">
                    Continue to Visual Content
                </button>
            </div>
        </div>
    `;
    document.getElementById('step2').insertAdjacentHTML('afterend', step3Html);
}

async function handleAudioUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    try {
        // Create audio element to get duration
        const audio = document.createElement('audio');
        audio.src = URL.createObjectURL(file);

        // Wait for metadata to load to get duration
        await new Promise((resolve, reject) => {
            audio.addEventListener('loadedmetadata', resolve);
            audio.addEventListener('error', reject);
        });

        // Store audio duration
        localStorage.setItem('audioDuration', audio.duration);

        // Store audio file temporarily
        const reader = new FileReader();
        reader.onload = function(e) {
            localStorage.setItem('audioData', e.target.result);
        };
        reader.readAsDataURL(file);

        // Enable continue button
        document.getElementById('visualContentBtn').disabled = false;
    } catch (error) {
        console.error('Error processing audio file:', error);
        alert('Error processing audio file. Please try again.');
    }
}

function proceedToVisualContent() {
    const script = localStorage.getItem('videoScript');
    const audioDuration = localStorage.getItem('audioDuration');

    if (!script || !audioDuration) {
        alert('Missing required data. Please ensure script and audio are properly loaded.');
        return;
    }

    // Show visual content step
    document.getElementById('step3').style.display = 'none';

    // Generate AI prompt for visual content
    const visualPrompt = `Based on the following script and audio duration of ${Math.ceil(audioDuration)} seconds, please provide a detailed visual storyboard that matches this exact format:

Script:
${script}

Required Format for Each Scene:
{
    "timestamp": "0:00",
    "duration": 5,
    "type": "image/video",
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

Please provide a complete timeline that covers the entire ${Math.ceil(audioDuration)} seconds of audio, with each scene following the exact format above. The program will use this format to automatically process the video.

Example Scene:
{
    "timestamp": "0:00",
    "duration": 5,
    "type": "image",
    "description": "Opening title card with company logo",
    "source": "Upload company logo image",
    "startTransition": "fade-in",
    "endTransition": "dissolve-out",
    "filter": "bright"
}
`;

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
                    <a href="https://bard.google.com" target="_blank" class="btn btn-outline-primary">Bard</a>
                </div>
            </div>

            <div class="mb-3">
                <h5>Find visual content:</h5>
                <div class="d-grid gap-2">
                    <a href="https://unsplash.com" target="_blank" class="btn btn-outline-primary">Unsplash (Free Images)</a>
                    <a href="https://pexels.com" target="_blank" class="btn btn-outline-primary">Pexels (Free Images & Videos)</a>
                    <a href="https://pixabay.com" target="_blank" class="btn btn-outline-primary">Pixabay (Free Media)</a>
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
        // Try to parse the response as JSON
        let timeline;
        try {
            timeline = JSON.parse(visualResponse);
        } catch (e) {
            // If direct parsing fails, try to extract JSON objects from the text
            const jsonMatches = visualResponse.match(/\{[\s\S]*?\}/g);
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

        // Sort timeline by timestamp
        timeline.sort((a, b) => {
            const timeA = a.timestamp.split(':').map(Number);
            const timeB = b.timestamp.split(':').map(Number);
            return (timeA[0] * 60 + timeA[1]) - (timeB[0] * 60 + timeB[1]);
        });

        // Save the validated and formatted timeline
        localStorage.setItem('visualTimeline', JSON.stringify(timeline));

        // Redirect to the editor page
        window.location.href = '/editor';
    } catch (error) {
        console.error('Error processing timeline:', error);
        alert('Error processing the visual timeline. Please ensure it follows the exact format shown in the prompt and try again.');
        return;
    }
}