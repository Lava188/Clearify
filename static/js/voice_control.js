document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    let isVoiceControlActive = false;
    let isSpeechPlaying = false;
    let currentUtterance = null;

    // Add voice control button to navbar
    const voiceControlButton = createVoiceControlButton();
    const navbarElement = document.querySelector('.nav-masthead');
    if (navbarElement) {
        navbarElement.appendChild(voiceControlButton);
    }

    // Create status area
    const statusArea = createStatusArea();
    const mainContainer = document.querySelector('main');
    if (mainContainer) {
        mainContainer.insertBefore(statusArea, mainContainer.firstChild);
    }

    // Handle Socket.IO events
    socket.on('redirect', function(data) {
        window.location.href = data.url;
    });

    socket.on('start_reading', function(data) {
        readText(data.text);
    });

    socket.on('stop_reading', function() {
        stopReading();
    });

    socket.on('capture_response', function(data) {
        if (data.success) {
            updateUI(data);
        } else {
            updateStatusMessage('Failed to capture image: ' + data.error, 'error');
        }
    });

    function toggleVoiceControl() {
        if (isVoiceControlActive) {
            fetch('/stop-voice-recognition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                isVoiceControlActive = false;
                voiceControlButton.classList.remove('active');
                updateStatusMessage('Voice control stopped', 'info');
            })
            .catch(error => {
                console.error('Error:', error);
                updateStatusMessage('Error stopping voice control', 'error');
            });
        } else {
            fetch('/start-voice-recognition', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                isVoiceControlActive = true;
                voiceControlButton.classList.add('active');
                updateStatusMessage('Voice control started. Try saying "capture", "read", or "stop"', 'success');
            })
            .catch(error => {
                console.error('Error:', error);
                updateStatusMessage('Error starting voice control', 'error');
            });
        }
    }

    function createVoiceControlButton() {
        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'hover-target';
        buttonContainer.onmouseover = function() { startSpeaking(this); };
        buttonContainer.onmouseout = function() { stopSpeaking(); };

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-light px-3 me-md-3 gap-3 fw-bold voice-control-btn';
        button.style.backgroundColor = '#F7F9F9';
        button.style.height = '50px';
        button.innerHTML = '<i class="fas fa-microphone"></i> Voice Control';
        button.onclick = toggleVoiceControl;

        buttonContainer.appendChild(button);
        return buttonContainer;
    }

    function createStatusArea() {
        const statusContainer = document.createElement('div');
        statusContainer.className = 'container align-items-center rounded-3 border shadow-lg mb-4';
        statusContainer.style.backgroundColor = '#FCF3CF';
        statusContainer.style.fontFamily = 'Georgia, serif';
        statusContainer.style.padding = '10px';
        statusContainer.style.marginTop = '20px';
        statusContainer.style.display = 'none';

        const statusText = document.createElement('p');
        statusText.className = 'status-message text-center';
        statusText.style.margin = '0';
        statusText.style.padding = '10px';
        statusText.style.fontWeight = 'bold';

        statusContainer.appendChild(statusText);
        return statusContainer;
    }

    function updateStatusMessage(message, type) {
        const statusArea = document.querySelector('.container.align-items-center.rounded-3.border.shadow-lg.mb-4');
        const statusText = document.querySelector('.status-message');
        
        if (statusArea && statusText) {
            statusText.textContent = message;
            if (type === 'error') {
                statusText.style.color = '#D63031';
            } else if (type === 'success') {
                statusText.style.color = '#27AE60';
            } else if (type === 'info') {
                statusText.style.color = '#3498DB';
            }
            statusArea.style.display = 'block';
            if (type !== 'error') {
                setTimeout(() => {
                    statusArea.style.display = 'none';
                }, 5000);
            }
        }
    }

    function readText(text) {
        if (text && !isSpeechPlaying) {
            stopReading();
            responsiveVoice.speak(text, 'UK English Female', {
                rate: 0.9,
                onstart: () => {
                    isSpeechPlaying = true;
                    updateStatusMessage('Reading text...', 'info');
                },
                onend: () => {
                    isSpeechPlaying = false;
                    updateStatusMessage('Finished reading text', 'success');
                }
            });
        } else {
            updateStatusMessage('No text to read or browser not supported', 'error');
        }
    }

    function stopReading() {
        if (isSpeechPlaying) {
            responsiveVoice.cancel();
            isSpeechPlaying = false;
            updateStatusMessage('Stopped reading text', 'info');
        }
    }

    function updateUI(data) {
        const textOutput = document.querySelector('.fs-4.fw-bold p');
        if (textOutput) {
            textOutput.textContent = data.text;
        }
        
        const audioElement = document.querySelector('#audioOutput');
        if (audioElement && data.audio_path) {
            audioElement.src = `/give_audio/${data.audio_path}`;
            audioElement.load();
            audioElement.play();
        }
        
        updateStatusMessage('Image captured and text recognized successfully', 'success');
    }

    function startSpeaking(element) {
        if (!isSpeechPlaying) {
            const textToRead = element.textContent;
            responsiveVoice.speak(textToRead, 'UK English Female', {
                rate: 0.9,
                onstart: () => {
                    isSpeechPlaying = true;
                },
                onend: () => {
                    isSpeechPlaying = false;
                }
            });
        }
    }

    function stopSpeaking() {
        if (isSpeechPlaying) {
            responsiveVoice.cancel();
            isSpeechPlaying = false;
        }
    }

    function checkInitialStatus() {
        fetch('/voice-status')
            .then(response => response.json())
            .then(data => {
                if (data.is_listening) {
                    isVoiceControlActive = true;
                    const voiceBtn = document.querySelector('.voice-control-btn');
                    if (voiceBtn) {
                        voiceBtn.classList.add('active');
                    }
                }
            })
            .catch(error => console.error('Error checking voice status:', error));
    }

    checkInitialStatus();
});

// Add Font Awesome for microphone icon
(function() {
    const fontAwesome = document.createElement('link');
    fontAwesome.rel = 'stylesheet';
    fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
    document.head.appendChild(fontAwesome);
})();