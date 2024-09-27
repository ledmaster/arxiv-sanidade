document.addEventListener('DOMContentLoaded', () => {
    fetchPapers();
    setupSavePaperForm();
});

function setupSavePaperForm() {
    const form = document.getElementById('save-form');
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const paperId = formData.get('paper_id');
        
        fetch('/save_paper', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ paper_id: paperId }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Paper saved successfully!');
                form.reset();
            } else {
                alert(data.message || 'An error occurred while saving the paper.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while saving the paper.');
        });
    });
}

function fetchPapers() {
    console.log('Fetching papers...');
    fetch('/papers')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(papers => {
            console.log('Received papers:', papers);
            if (papers.length === 0) {
                console.log('No papers received');
                return;
            }
            const papersDiv = document.getElementById('papers');
            papersDiv.innerHTML = '';
            papers.forEach(paper => {
                const paperDiv = document.createElement('div');
                paperDiv.className = 'paper';
                paperDiv.innerHTML = `
                <h2>${paper.title}</h2>
                <p class="submission-date">Updated: ${formatDate(paper.published)}</p>
                <p class="score">Score: ${paper.score.toFixed(4)}</p>
                <p>${paper.abstract}</p>
                <div class="paper-actions">
                    <button class="save-paper" data-paper-id="${paper.id}">Save Paper</button>
                    <a href="${paper.id.replace('abs', 'pdf')}" target="_blank" class="view-pdf">View PDF</a>
                    <button class="copy-link" data-paper-id="${paper.id}">Copy Link</button>
                </div>
            `;
                papersDiv.appendChild(paperDiv);
            });
            addSavePaperListeners();
            addCopyLinkListeners();
        })
        .catch(error => {
            console.error('Error fetching papers:', error);
        });
}

function addCopyLinkListeners() {
    const copyButtons = document.querySelectorAll('.copy-link');
    copyButtons.forEach(button => {
        button.addEventListener('click', () => {
            const paperId = button.dataset.paperId;
            copyPaperLink(paperId);
        });
    });
}

function copyPaperLink(paperId) {
    navigator.clipboard.writeText(paperId)
        .then(() => {
            console.log('Paper ID copied to clipboard!');
        })
        .catch(err => {
            console.error('Failed to copy paper ID: ', err);
            alert('Failed to copy paper ID. Please try again.');
        });
}

function addSavePaperListeners() {
    const saveButtons = document.querySelectorAll('.save-paper');
    saveButtons.forEach(button => {
        button.addEventListener('click', () => {
            const paperId = button.dataset.paperId;
            savePaper(paperId);
        });
    });
}

function savePaper(paperId) {
    fetch('/save_paper', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ paper_id: paperId }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Paper saved successfully!');
        } else {
            alert(data.message || 'An error occurred while saving the paper.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while saving the paper.');
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}