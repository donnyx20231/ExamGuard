document.addEventListener('DOMContentLoaded', () => {
    console.log('Exam page DOM content loaded.');

    const startExamContainer = document.getElementById('start-exam-container');
    const startExamButton = document.getElementById('start-exam-button');
    const examContainer = document.getElementById('exam-container');
    const examTitle = document.getElementById('exam-title');
    const timerDisplay = document.getElementById('timer');
    const questionsContainer = document.getElementById('questions-container');
    const submitButton = document.getElementById('submit-exam');
    const cheatingWarning = document.getElementById('cheating-warning');
    const warningsContainer = document.getElementById('warnings-container');
    const agreeToWarningsButton = document.getElementById('agree-to-warnings');
    const questionNavigation = document.getElementById('question-navigation');
    const returnToFullScreenButton = document.getElementById('return-to-fullscreen');
    const pathParts = window.location.pathname.split('/');
    const courseCode = pathParts[3];
    const attemptId = pathParts[4];

    let examDeadline;
    let questions = [];
    let currentQuestionIndex = 0;
    let cheatingAttempts = 0;
    let examSubmitted = false;

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
        questionsContainer.innerHTML = ''; // Clear previous question

        // --- Create Question Navigation ---
        questionNavigation.innerHTML = '';
        questions.forEach((q, index) => {
            const button = document.createElement('button');
            button.textContent = index + 1;
            button.classList.add('question-nav-button');
            if (index === currentQuestionIndex) {
                button.classList.add('active');
            }
            if (q.answered) {
                button.classList.add('answered');
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
                    <input type="radio" name="question-${question.id}" value="${option.id}" id="option-${option.id}" onchange="markAsAnswered()">
                    <label for="option-${option.id}">${option.option_text}</label>
                `;
                optionsList.appendChild(optionItem);
            });
            questionDiv.appendChild(optionsList);
        } else if (question.question_type === 'fill_in_the_blanks') {
            const input = document.createElement('input');
            input.type = 'text';
            input.name = `question-${question.id}`;
            input.oninput = markAsAnswered;
            questionDiv.appendChild(input);
        } else if (question.question_type === 'essay') {
            const textarea = document.createElement('textarea');
            textarea.name = `question-${question.id}`;
            textarea.rows = 5;
            textarea.oninput = markAsAnswered;
            questionDiv.appendChild(textarea);
        }

        questionsContainer.appendChild(questionDiv);

        const navigationDiv = document.createElement('div');
        navigationDiv.classList.add('navigation');

        if (currentQuestionIndex > 0) {
            const prevButton = document.createElement('button');
            prevButton.textContent = 'Previous';
            prevButton.addEventListener('click', () => {
                currentQuestionIndex--;
                displayCurrentQuestion();
            });
            navigationDiv.appendChild(prevButton);
        }

        if (currentQuestionIndex < questions.length - 1) {
            const nextButton = document.createElement('button');
            nextButton.textContent = 'Next';
            nextButton.addEventListener('click', () => {
                currentQuestionIndex++;
                displayCurrentQuestion();
            });
            navigationDiv.appendChild(nextButton);
        }

        questionsContainer.appendChild(navigationDiv);
        attachBlockListenersToFields();
    };

    const markAsAnswered = () => {
        questions[currentQuestionIndex].answered = true;
        displayCurrentQuestion();
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
        const answers = [];
        questions.forEach((question, index) => {
            const questionElement = document.querySelector('.question');
            if (questionElement) {
                const questionId = question.id;
                let answer = { question_id: questionId };
                const inputElement = questionElement.querySelector('input, textarea');
                if (inputElement) {
                    if (inputElement.type === 'radio') {
                        const checkedOption = questionElement.querySelector('input[type="radio"]:checked');
                        if (checkedOption) {
                            answer.selected_option_id = parseInt(checkedOption.value);
                        }
                    } else {
                        if (inputElement.value.trim() !== '') {
                            answer.answer_text = inputElement.value;
                        }
                    }
                }
                answers.push(answer);
            }
        });

        try {
            const response = await fetch(`/api/student/exam/${courseCode}/submit/?attempt_id=${attemptId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ answers }),
            });

            const data = await response.json();

            if (response.ok) {
                alert(`Exam submitted successfully! Your score is: ${data.final_score}`);
                window.location.href = '/student/login/';
            } else {
                alert(data.error || 'Failed to submit the exam.');
            }
        } catch (error) {
            console.error('Error submitting exam:', error);
            alert('An error occurred while submitting the exam.');
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
            alert('You have reached the maximum number of violations. Your exam will be submitted.');
            submitExam();
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

    if (submitButton) {
        submitButton.addEventListener('click', submitExam);
    }

    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            if (cheatingWarning) cheatingWarning.style.display = 'flex';
            handleCheatingAttempt();
        } else {
            if (cheatingWarning) cheatingWarning.style.display = 'none';
        }
    });
    
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            handleCheatingAttempt();
        }
    });

    if (returnToFullScreenButton) {
        returnToFullScreenButton.addEventListener('click', () => {
            enterFullScreen();
        });
    }

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
});