document.addEventListener('DOMContentLoaded', function() {
    AOS.init({
        duration: 1000,
        easing: 'ease-in-out',
        once: true
    });

    // Set the current year in the footer
    document.getElementById('current-year').textContent = new Date().getFullYear();
});

document.getElementById('file-input').addEventListener('change', (event) => {
    const fileName = event.target.files[0]?.name || 'No file selected';
    document.getElementById('file-name').textContent = `Selected file: ${fileName}`;
});

document.getElementById('upload-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData();
    const fileInput = document.getElementById('file-input');
    formData.append('file', fileInput.files[0]);

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    const result = await response.json();
    if (result.error) {
        document.getElementById('result').innerHTML = `<div class="alert alert-danger">${result.error}</div>`;
    } else {
        const columnSelect = document.getElementById('column-select');
        columnSelect.innerHTML = '';  // Clear any previous options

        result.columns.forEach(column => {
            const option = document.createElement('option');
            option.value = column;
            option.textContent = column;
            columnSelect.appendChild(option);
        });

        document.getElementById('column-selection').style.display = 'block';
        document.getElementById('process-file').onclick = async () => {
            const selectedColumn = columnSelect.value;

            // Display the loading bar container here to avoid initial appearance
            document.getElementById('loading-bar-container').style.display = 'block';
            document.getElementById('loading-bar').style.width = '0%';

            const processResponse = await fetch('/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ file_path: result.file_path, email_column: selectedColumn })
            });

            const processResult = await processResponse.json();
            if (processResult.error) {
                document.getElementById('result').innerHTML = `<div class="alert alert-danger">${processResult.error}</div>`;
            } else {
                const taskId = processResult.task_id;

                const interval = setInterval(async () => {
                    const progressResponse = await fetch(`/progress/${taskId}`);
                    const progressResult = await progressResponse.json();

                    if (progressResult.progress >= 100) {
                        clearInterval(interval);
                        document.getElementById('loading-bar').style.width = '100%';

                        const downloadLink = document.createElement('a');
                        downloadLink.href = `/download/${result.file_path.split('.').slice(0, -1).join('.')}-esp.csv`;
                        downloadLink.textContent = 'Download Processed CSV';
                        downloadLink.className = 'btn btn-primary btn-lg mt-3';
                        downloadLink.download = downloadLink.href.split('/').pop();
                        document.getElementById('result').innerHTML = '';  // Clear any previous content
                        document.getElementById('result').appendChild(downloadLink);

                        setTimeout(() => {
                            document.getElementById('loading-bar-container').style.display = 'none';
                        }, 500); // Adjust the delay as needed
                    } else {
                        document.getElementById('loading-bar').style.width = `${progressResult.progress}%`;
                    }
                }, 1000);
            }
        };
    }
});

// Single Email Identification
document.getElementById('identify-email-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const emailInput = document.getElementById('single-email-input').value;

    const response = await fetch('/identify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email: emailInput })
    });

    const result = await response.json();
    if (result.error) {
        document.getElementById('single-email-result').innerHTML = `<div class="alert alert-danger">${result.error}</div>`;
    } else {
        document.getElementById('single-email-result').innerHTML = `<div class="alert alert-success">Email: ${result.email}<br>ESP: ${result.esp}</div>`;
    }
});
