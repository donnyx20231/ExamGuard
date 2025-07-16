document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const errorMessage = document.getElementById('error-message');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorMessage.textContent = '';

        const name = document.getElementById('name').value;
        const matricNumber = document.getElementById('matric_number').value;
        const courseCode = document.getElementById('course_code').value;

        try {
            const response = await fetch('/api/student/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name,
                    matric_number: matricNumber,
                    course_code: courseCode,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // Redirect to the exam page with the attempt ID
                window.location.href = `/student/exam/${courseCode}/${data.exam_attempt_id}/`;
            } else {
                errorMessage.textContent = data.error || 'An unknown error occurred.';
            }
        } catch (error) {
            errorMessage.textContent = 'An error occurred while trying to log in.';
            console.error('Login error:', error);
        }
    });
}); 