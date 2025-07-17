document.addEventListener('DOMContentLoaded', () => {
    console.log('Exam page DOM content loaded.');

    const startExamContainer = document.getElementById('start-exam-container');
    const startExamButton = document.getElementById('start-exam-button');
    const examContainer = document.getElementById('exam-container');
    const examTitle = document.getElementById('exam-title');
    const timerDisplay = document.getElementById('timer');
    const questionsContainer = document.getElementById('questions-container');
    const submitButton = document.getElementById('submit-exam');
    const prevButton = document.getElementById('prev-question');
    const nextButton = document.getElementById('next-question');
    const cheatingWarning = document.getElementById('cheating-warning');
    const questionNavigation = document.getElementById('question-navigation');
    const violationWarning = document.getElementById('violation-warning');
    const examProgressBar = document.getElementById('exam-progress-bar');
    const examProgressStats = document.getElementById('exam-progress-stats');
    const studentInfo = document.getElementById('student-info');
    const fullscreenStatus = document.getElementById('fullscreen-status');
    const warningsContainer = document.getElementById('warnings-container');
    const agreeToWarningsButton = document.getElementById('agree-to-warnings');
    const returnToFullScreenButton = document.getElementById('return-to-fullscreen');
    const pathParts = window.location.pathname.split('/');
    const courseCode = pathParts[3];
    const attemptId = pathParts[4];

    let examDeadline;
    let questions = [];
    let currentQuestionIndex = 0;
    let cheatingAttempts = 0;
    let examSubmitted = false;
    let studentAnswers = {}; // Store answers for all questions

    const fetchQuestions = async () => {
        console.log('Fetching questions...');
        try {
            const response = await fetch(`/api/student/exam/${courseCode}/questions/?attempt_id=${attemptId}`);
            const data = await response.json();

            if (response.ok) {
                examTitle.textContent = data.exam_title;
                examDeadline = new Date(data.attempt_deadline);
                questions = data.questions.map(q => ({ ...q, answered: false })); // Add answered property
                displayCurrentQuestion();
                startTimer();
            } else {
                alert(data.error || 'Failed to fetch exam questions.');
            }
        } catch (error) {
            console.error('Error fetching questions:', error);
            alert('An error occurred while fetching the exam questions.');
        }
    };

    const displayCurrentQuestion = () => {
        const question = questions[currentQuestionIndex];
        questionsContainer.innerHTML = '';

        // --- Create Question Navigation in Sidebar ---
        questionNavigation.innerHTML = '';
        questions.forEach((q, index) => {
            const button = document.createElement('button');
            button.textContent = index + 1;
            button.classList.add('question-nav-button');
            if (index === currentQuestionIndex) {
                button.classList.add('active');
            }
            if (q.answered) {
                button.classList.add('answered'); // now red
            } else {
                button.classList.add('not-answered');
            }
            button.addEventListener('click', () => {
                currentQuestionIndex = index;
                displayCurrentQuestion();
            });
            questionNavigation.appendChild(button);
        });

        const questionDiv = document.createElement('div');
        questionDiv.classList.add('question');
        questionDiv.innerHTML = `<p>${currentQuestionIndex + 1}. ${question.question_text}</p>`;

        if (question.question_type === 'multiple_choice') {
            const optionsList = document.createElement('ul');
            optionsList.classList.add('options');
            question.options.forEach(option => {
                const optionItem = document.createElement('li');
                optionItem.innerHTML = `
                    <input type="radio" name="question-${question.id}" value="${option.id}" id="option-${option.id}">
                    <label for="option-${option.id}">${option.option_text}</label>
                `;
                optionsList.appendChild(optionItem);
            });
            questionDiv.appendChild(optionsList);
        } else if (question.question_type === 'fill_in_the_blanks') {
            const input = document.createElement('input');
            input.type = 'text';
            input.name = `question-${question.id}`;
            questionDiv.appendChild(input);
        } else {
            const textarea = document.createElement('textarea');
            textarea.name = `question-${question.id}`;
            textarea.rows = 5;
            questionDiv.appendChild(textarea);
        }

        // Restore previous answer if exists
        if (studentAnswers[question.id]) {
            if (question.question_type === 'multiple_choice') {
                const selectedOption = studentAnswers[question.id].selected_option_id;
                if (selectedOption) {
                    const radio = questionDiv.querySelector(`input[type="radio"][value="${selectedOption}"]`);
                    if (radio) radio.checked = true;
                }
            } else {
                const input = questionDiv.querySelector('input, textarea');
                if (input) input.value = studentAnswers[question.id].answer_text || '';
            }
        }

        questionsContainer.appendChild(questionDiv);
        attachBlockListenersToFields();

        // Add event listeners to save answers
        if (question.question_type === 'multiple_choice') {
            questionDiv.querySelectorAll('input[type="radio"]').forEach(radio => {
                radio.addEventListener('change', (e) => {
                    studentAnswers[question.id] = { question_id: question.id, selected_option_id: parseInt(e.target.value) };
                    questions[currentQuestionIndex].answered = true;
                    updateProgress();
                    displayCurrentQuestion();
                });
            });
        } else {
            const input = questionDiv.querySelector('input, textarea');
            if (input) {
                input.addEventListener('input', (e) => {
                    studentAnswers[question.id] = { question_id: question.id, answer_text: e.target.value };
                    questions[currentQuestionIndex].answered = !!e.target.value.trim();
                    updateProgress();
                    displayCurrentQuestion();
                });
            }
        }
    };

    const startTimer = () => {
        const timerInterval = setInterval(() => {
            const now = new Date();
            const timeLeft = examDeadline - now;

            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                timerDisplay.textContent = 'Time\'s up!';
                submitExam();
            } else {
                const minutes = Math.floor((timeLeft / 1000 / 60) % 60);
                const seconds = Math.floor((timeLeft / 1000) % 60);
                timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    };

    const submitExam = async () => {
        if (examSubmitted) return;
        examSubmitted = true;
        console.log('Submitting exam...');
        const answers = Object.values(studentAnswers);
        console.log('Answers being sent:', answers);

        try {
            const response = await fetch(`/api/student/exam/${courseCode}/submit/?attempt_id=${attemptId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers }),
            });

            const data = await response.json();
            console.log('Backend response:', data);

            if (response.ok) {
                // Store result and summary in localStorage
                localStorage.setItem('exam_score', data.final_score);
                localStorage.setItem('exam_total', data.total_marks_possible);
                // Prepare summary: answered/skipped for each question
                const summary = questions.map(q => ({ answered: !!studentAnswers[q.id] && (studentAnswers[q.id].selected_option_id || (studentAnswers[q.id].answer_text && studentAnswers[q.id].answer_text.trim())) }));
                localStorage.setItem('exam_summary', JSON.stringify(summary));
                window.location.href = '/student/result/';
            } else {
                alert(data.error || 'Failed to submit the exam.');
            }
        } catch (error) {
            console.error('Error submitting exam:', error);
            alert('An error occurred while submitting the exam. Check the console for details.');
        }
    };

    const enterFullScreen = () => {
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen();
        } else if (document.documentElement.mozRequestFullScreen) { /* Firefox */
            document.documentElement.mozRequestFullScreen();
        } else if (document.documentElement.webkitRequestFullscreen) { /* Chrome, Safari and Opera */
            document.documentElement.webkitRequestFullscreen();
        } else if (document.documentElement.msRequestFullscreen) { /* IE/Edge */
            document.documentElement.msRequestFullscreen();
        }
    };

    const logCheatingAttempt = async () => {
        try {
            await fetch(`/api/student/exam/${courseCode}/log_cheating_attempt/?attempt_id=${attemptId}`, { method: 'POST' });
        } catch (error) {
            console.error('Error logging cheating attempt:', error);
        }
    };

    const handleCheatingAttempt = () => {
        cheatingAttempts++;
        logCheatingAttempt();
        if (cheatingAttempts >= 3) {
            alert('You have reached the maximum number of violations. You will be logged out.');
            submitExam();
            setTimeout(() => {
                window.location.href = '/student/login/';
            }, 1000);
            // Optionally, disable further input
            document.querySelectorAll('input, textarea, button').forEach(el => {
                if (el.id !== 'submit-exam') el.disabled = true;
            });
        }
    };

    // Robust copy/paste/selection blocking
    function blockCopyPaste(e) {
        e.preventDefault();
        handleCheatingAttempt();
        alert('Copying and pasting are disabled during the exam.');
        return false;
    }

    // Block copy/paste globally
    document.addEventListener('copy', blockCopyPaste);
    document.addEventListener('cut', blockCopyPaste);
    document.addEventListener('paste', blockCopyPaste);
    document.addEventListener('contextmenu', function(e) {
        e.preventDefault();
        handleCheatingAttempt();
        alert('Right-click is disabled during the exam.');
        return false;
    });

    // Block keyboard shortcuts (Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && ['c', 'v', 'x', 'a'].includes(e.key.toLowerCase())) {
            e.preventDefault();
            handleCheatingAttempt();
            alert('Keyboard shortcuts for copy, paste, cut, and select all are disabled during the exam.');
            return false;
        }
    });

    // Also block on all input and textarea fields
    function attachBlockListenersToFields() {
        document.querySelectorAll('input, textarea').forEach(field => {
            field.addEventListener('copy', blockCopyPaste);
            field.addEventListener('cut', blockCopyPaste);
            field.addEventListener('paste', blockCopyPaste);
            field.addEventListener('contextmenu', blockCopyPaste);
            field.addEventListener('keydown', function(e) {
                if ((e.ctrlKey || e.metaKey) && ['c', 'v', 'x', 'a'].includes(e.key.toLowerCase())) {
                    e.preventDefault();
                    handleCheatingAttempt();
                    alert('Keyboard shortcuts for copy, paste, cut, and select all are disabled during the exam.');
                    return false;
                }
            });
        });
    }

    // --- Event Listeners ---
    if (agreeToWarningsButton) {
        agreeToWarningsButton.addEventListener('click', () => {
            if (warningsContainer) warningsContainer.style.display = 'none';
            if (startExamContainer) startExamContainer.style.display = 'flex';
        });
    }

    if (startExamButton) {
        startExamButton.addEventListener('click', () => {
            if (startExamContainer) startExamContainer.style.display = 'none';
            if (examContainer) examContainer.style.display = 'block';
            enterFullScreen();
            fetchQuestions();
        });
    }

    // Fill in student info (example: from global context or API)
    if (studentInfo) {
        // Example: Replace with actual student info from backend/session
        studentInfo.textContent = window.studentName ? `${window.studentName} | ${window.studentId}` : '';
    }
    // Fullscreen status
    function updateFullscreenStatus() {
        if (fullscreenStatus) {
            if (document.fullscreenElement) {
                fullscreenStatus.textContent = 'Fullscreen Active';
                fullscreenStatus.style.color = '#388e3c';
            } else {
                fullscreenStatus.textContent = 'Fullscreen Inactive';
                fullscreenStatus.style.color = '#d32f2f';
            }
        }
    }
    document.addEventListener('fullscreenchange', updateFullscreenStatus);
    updateFullscreenStatus();

    // Violation warning update
    function setViolationWarning(remaining) {
        if (violationWarning) {
            violationWarning.textContent = `${remaining} violation${remaining === 1 ? '' : 's'} remaining before automatic submission.`;
        }
    }
    let maxViolations = 3;
    let currentViolations = 0;
    setViolationWarning(maxViolations - currentViolations);

    // Navigation button wiring
    if (prevButton) {
        prevButton.onclick = () => {
            if (currentQuestionIndex > 0) {
                currentQuestionIndex--;
                displayCurrentQuestion();
            }
        };
    }
    if (nextButton) {
        nextButton.onclick = () => {
            if (currentQuestionIndex < questions.length - 1) {
                currentQuestionIndex++;
                displayCurrentQuestion();
            }
        };
    }
    if (submitButton) {
        submitButton.onclick = submitExam;
    }

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            handleCheatingAttempt();
        }
    });

    // --- Fullscreen Enforcement ---
    function requireFullscreen() {
        if (!document.fullscreenElement) {
            if (cheatingWarning) cheatingWarning.style.display = 'flex';
        } else {
            if (cheatingWarning) cheatingWarning.style.display = 'none';
        }
    }
    // Always show 'Return to Fullscreen' button when not in fullscreen
    if (returnToFullScreenButton) {
        returnToFullScreenButton.onclick = () => {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            } else if (document.documentElement.mozRequestFullScreen) {
                document.documentElement.mozRequestFullScreen();
            } else if (document.documentElement.webkitRequestFullscreen) {
                document.documentElement.webkitRequestFullscreen();
            } else if (document.documentElement.msRequestFullscreen) {
                document.documentElement.msRequestFullscreen();
            }
        };
    }
    document.addEventListener('fullscreenchange', () => {
        updateFullscreenStatus();
        requireFullscreen();
    });
    // On page load, require fullscreen
    window.onload = () => {
        requireFullscreen();
        if (!document.fullscreenElement) {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            }
        }
        // Fetch questions after entering fullscreen
        fetchQuestions();
    };

    // 4. Attempt to disable print screen
    document.addEventListener('keyup', (e) => {
        if (e.key == 'PrintScreen') {
            navigator.clipboard.writeText('');
            handleCheatingAttempt();
            alert('Screenshots are not allowed during the exam.');
        }
    });
    // 5. Attempt to disable screenshot on mobile
    window.addEventListener('screenshot', () => {
        handleCheatingAttempt();
        alert('Screenshots are not allowed during the exam.');
    });
    
    // Attach listeners initially
    attachBlockListenersToFields();

    // Progress bar and stats update
    function updateProgress() {
        if (!questions.length) return;
        const answered = questions.filter(q => q.answered).length;
        const total = questions.length;
        if (examProgressBar) {
            let percent = Math.round((answered / total) * 100);
            examProgressBar.innerHTML = `<div class='progress' style='width:${percent}%;'></div>`;
        }
        if (examProgressStats) {
            examProgressStats.textContent = `${answered} of ${total} questions answered`;
        }
    }
    // Call updateProgress after each question change
    const origDisplayCurrentQuestion = displayCurrentQuestion;
    displayCurrentQuestion = function() {
        origDisplayCurrentQuestion.apply(this, arguments);
        updateProgress();
    };
    // Initial progress update
    updateProgress();
});