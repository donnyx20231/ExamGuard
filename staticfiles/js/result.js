document.addEventListener('DOMContentLoaded', () => {
    // Get result data from localStorage
    const score = localStorage.getItem('exam_score');
    const total = localStorage.getItem('exam_total');
    const summary = JSON.parse(localStorage.getItem('exam_summary') || '[]');

    document.getElementById('score').textContent = `Your Score: ${score} / ${total}`;

    const summaryList = document.getElementById('question-summary');
    summary.forEach((q, idx) => {
        const li = document.createElement('li');
        li.style.marginBottom = '0.5rem';
        li.innerHTML = `<strong>Q${idx + 1}:</strong> ${q.answered ? '<span style="color: #28a745;">Answered</span>' : '<span style="color: #dc3545;">Skipped</span>'}`;
        summaryList.appendChild(li);
    });

    // Optionally clear after showing
    localStorage.removeItem('exam_score');
    localStorage.removeItem('exam_total');
    localStorage.removeItem('exam_summary');
}); 