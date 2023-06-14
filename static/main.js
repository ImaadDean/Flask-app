function previewImage(event) {
    const input = event.target;
    const preview = document.getElementById('imagePreview');

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function (e) {
            const image = document.createElement('img');
            image.src = e.target.result;
            image.classList.add('mt-2', 'max-w-full', 'rounded-md');
            image.style.objectFit = 'cover';
            image.style.maxHeight = '200px'; // Adjust the maximum height as desired
            preview.innerHTML = '';
            preview.appendChild(image);
        };

        reader.readAsDataURL(input.files[0]);
    } else {
        preview.innerHTML = '';
    }
}