document.addEventListener('DOMContentLoaded', () => {
    const examTitle = document.getElementById('exam-title');
    const timerDisplay = document.getElementById('timer');
    const questionsContainer = document.getElementById('questions-container');
    const submitButton = document.getElementById('submit-exam');
    const cheatingWarning = document.getElementById('cheating-warning');
    const courseCode = window.location.pathname.split('/')[3];

    let examDeadline;

    const fetchQuestions = async () => {
        try {
            const response = await fetch(`/api/exam/${courseCode}/questions/`);
            const data = await response.json();

            if (response.ok) {
                examTitle.textContent = data.exam_title;
                examDeadline = new Date(data.attempt_deadline);
                displayQuestions(data.questions);
                startTimer();
            } else {
                alert(data.error || 'Failed to fetch exam questions.');
            }
        } catch (error) {
            console.error('Error fetching questions:', error);
            alert('An error occurred while fetching the exam questions.');
        }
    };

    const displayQuestions = (questions) => {
        questions.forEach((question, index) => {
            const questionDiv = document.createElement('div');
            questionDiv.classList.add('question');
            questionDiv.innerHTML = `<p>${index + 1}. ${question.question_text}</p>`;

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
            } else if (question.question_type === 'essay') {
                const textarea = document.createElement('textarea');
                textarea.name = `question-${question.id}`;
                textarea.rows = 5;
                questionDiv.appendChild(textarea);
            }

            questionsContainer.appendChild(questionDiv);
        });
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
        const answers = [];
        const questions = document.querySelectorAll('.question');
        questions.forEach(question => {
            const questionId = parseInt(question.querySelector('input, textarea').name.split('-')[1]);
            let answer = { question_id: questionId };

            if (question.querySelector('input[type="radio"]:checked')) {
                answer.selected_option_id = parseInt(question.querySelector('input[type="radio"]:checked').value);
            } else if (question.querySelector('input[type="text"]')) {
                answer.answer_text = question.querySelector('input[type="text"]').value;
            } else if (question.querySelector('textarea')) {
                answer.answer_text = question.querySelector('textarea').value;
            }
            answers.push(answer);
        });

        try {
            const response = await fetch(`/api/exam/${courseCode}/submit/`, {
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

    const exitFullScreen = () => {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.mozCancelFullScreen) { /* Firefox */
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) { /* Chrome, Safari and Opera */
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) { /* IE/Edge */
            document.msExitFullscreen();
        }
    };

    const logCheatingAttempt = async () => {
        try {
            await fetch(`/api/exam/${courseCode}/log_cheating_attempt/`, { method: 'POST' });
        } catch (error) {
            console.error('Error logging cheating attempt:', error);
        }
    };

    // --- Security Measures ---

    // 1. Full-screen enforcement
    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            cheatingWarning.style.display = 'flex';
            logCheatingAttempt();
        } else {
            cheatingWarning.style.display = 'none';
        }
    });
    
    // 2. Disable copy-paste
    document.addEventListener('copy', (e) => {
        e.preventDefault();
        logCheatingAttempt();
    });
    document.addEventListener('paste', (e) => {
        e.preventDefault();
        logCheatingAttempt();
    });

    // 3. Detect leaving the page
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden') {
            logCheatingAttempt();
        }
    });

    // --- Initialization ---
    fetchQuestions();
    submitButton.addEventListener('click', submitExam);
    
    // Prompt user to enter full-screen
    alert('This exam must be taken in full-screen mode. Please click "OK" to enter full-screen.');
    enterFullScreen();
}); 