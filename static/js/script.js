document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');
    const resultsSection = document.getElementById('resultsSection');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const originalImage = document.getElementById('originalImage');
    const processedImage = document.getElementById('processedImage');
    const damageItems = document.getElementById('damageItems');
    const damageCount = document.getElementById('damageCount');
    const analysisDate = document.getElementById('analysisDate');
    const averageConfidence = document.getElementById('averageConfidence');
    const damageTypes = document.getElementById('damageTypes');
    const downloadReport = document.getElementById('downloadReport');

    // Event Listeners
    uploadBox.addEventListener('dragover', handleDragOver);
    uploadBox.addEventListener('dragleave', handleDragLeave);
    uploadBox.addEventListener('drop', handleDrop);
    uploadBox.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);
    downloadReport.addEventListener('click', downloadReportHandler);

    // Functions
    function handleDragOver(e) {
        e.preventDefault();
        uploadBox.classList.add('dragover');
    }

    function handleDragLeave() {
        uploadBox.classList.remove('dragover');
    }

    function handleDrop(e) {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload();
        }
    }

    async function handleFileUpload() {
        const file = fileInput.files[0];
        if (!file) return;

        // Validate file
        const validTypes = ['image/jpeg', 'image/png'];
        if (!validTypes.includes(file.type)) {
            alert('Please upload a valid image (JPEG or PNG)');
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            alert('File size exceeds 16MB limit');
            return;
        }

        // Show loading
        loadingOverlay.classList.add('active');
        resultsSection.style.display = 'none';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            if (data.status !== 'success') {
                throw new Error(data.message || 'Processing failed');
            }

            console.log('Server response:', data);

            // Display images with cache busting
            originalImage.src = data.data.image_paths.original + '?t=' + Date.now();
            processedImage.src = data.data.image_paths.processed + '?t=' + Date.now();

            // Error handling for images
            originalImage.onerror = () => {
                console.error('Failed to load original image:', originalImage.src);
            };
            processedImage.onerror = () => {
                console.error('Failed to load processed image:', processedImage.src);
            };

            // Update damage count
            damageCount.textContent = data.data.statistics.total_damages;

            // Update analysis info
            analysisDate.textContent = data.timestamp;
            averageConfidence.textContent = `${Math.round(data.data.statistics.confidence.average * 100)}%`;
            damageTypes.textContent = data.data.statistics.damage_types.join(', ') || 'None';

            // Update damage items
            damageItems.innerHTML = '';
            data.data.predictions.forEach(damage => {
                const item = document.createElement('div');
                item.className = 'damage-item';
                item.innerHTML = `
                    <span class="damage-type">${damage.class}</span>
                    <span class="damage-confidence">${Math.round(damage.confidence * 100)}%</span>
                `;
                damageItems.appendChild(item);
            });

            // Show results
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Upload failed:', error);
            alert('Error: ' + error.message);
        } finally {
            loadingOverlay.classList.remove('active');
        }
    }

    function downloadReportHandler() {
        alert('Report download would be implemented here');
        // In production: Generate PDF report
    }

    // Initial setup
    resultsSection.style.display = 'none';
});