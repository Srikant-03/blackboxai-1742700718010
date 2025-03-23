// Three.js Background Animation
function initBackgroundAnimation() {
    const container = document.getElementById('canvas-container');
    if (!container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    // Create particles
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for (let i = 0; i < 5000; i++) {
        vertices.push(
            Math.random() * 2000 - 1000,
            Math.random() * 2000 - 1000,
            Math.random() * 2000 - 1000
        );
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    const material = new THREE.PointsMaterial({ 
        color: 0x00ff88, 
        size: 2,
        transparent: true,
        opacity: 0.6
    });
    const points = new THREE.Points(geometry, material);
    scene.add(points);

    camera.position.z = 1000;

    // Add mouse interaction
    let mouseX = 0;
    let mouseY = 0;
    let targetRotationX = 0;
    let targetRotationY = 0;

    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX - window.innerWidth / 2) / 100;
        mouseY = (event.clientY - window.innerHeight / 2) / 100;
    });

    function animate() {
        requestAnimationFrame(animate);

        // Smooth rotation
        targetRotationX += (mouseY - targetRotationX) * 0.05;
        targetRotationY += (mouseX - targetRotationY) * 0.05;

        points.rotation.x = targetRotationX * 0.1;
        points.rotation.y = targetRotationY * 0.1;

        renderer.render(scene, camera);
    }

    animate();

    // Handle window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// Utility Functions
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// UI Animation Functions
function showLoading(element) {
    if (!element) return;
    element.style.opacity = '0';
    element.classList.remove('hidden');
    setTimeout(() => {
        element.style.opacity = '1';
    }, 10);
}

function hideLoading(element) {
    if (!element) return;
    element.style.opacity = '0';
    setTimeout(() => {
        element.classList.add('hidden');
    }, 300);
}

function showResults(element) {
    if (!element) return;
    element.style.opacity = '0';
    element.classList.remove('hidden');
    setTimeout(() => {
        element.style.opacity = '1';
        element.style.transform = 'translateY(0)';
    }, 10);
}

// File Upload Validation
function validateFile(file, type) {
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
        alert(`File size exceeds 50MB limit. Current size: ${formatBytes(file.size)}`);
        return false;
    }

    const allowedTypes = {
        image: ['image/jpeg', 'image/png', 'image/webp'],
        video: ['video/mp4', 'video/quicktime', 'video/x-msvideo']
    };

    if (!allowedTypes[type].includes(file.type)) {
        alert(`Invalid file type. Allowed types: ${allowedTypes[type].join(', ')}`);
        return false;
    }

    return true;
}

// Progress Bar Animation
function updateProgress(element, progress) {
    if (!element) return;
    const bar = element.querySelector('.progress-bar');
    if (bar) {
        bar.style.width = `${progress}%`;
    }
}

// Frame Timeline Visualization
function createFrameTimeline(container, frameData) {
    if (!container || !frameData) return;
    
    container.innerHTML = '';
    const width = container.offsetWidth;
    
    frameData.forEach((frame, index) => {
        const marker = document.createElement('div');
        marker.className = 'timeline-marker';
        marker.style.left = `${(index / frameData.length) * 100}%`;
        marker.style.height = `${frame.score * 100}%`;
        marker.title = `Time: ${frame.timestamp}s\nScore: ${Math.round(frame.score * 100)}%`;
        container.appendChild(marker);
    });
}

// Face Detection Visualization
function drawFaceDetectionBoxes(container, faces) {
    if (!container || !faces) return;
    
    // Clear previous boxes
    container.querySelectorAll('.face-detection-box').forEach(box => box.remove());
    
    faces.forEach(face => {
        const box = document.createElement('div');
        box.className = 'face-detection-box';
        box.style.left = `${face.x}px`;
        box.style.top = `${face.y}px`;
        box.style.width = `${face.width}px`;
        box.style.height = `${face.height}px`;
        box.setAttribute('data-confidence', `${Math.round(face.confidence * 100)}%`);
        container.appendChild(box);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initBackgroundAnimation();

    // Add smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});