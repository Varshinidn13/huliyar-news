(function () {
  var SOURCE_LIMIT = 500 * 1024;
  var TARGET_LIMIT = 300 * 1024;
  var MAX_EDGE = 1280;

  function canCompress(file) {
    return file && file.type && file.type.indexOf('image/') === 0 && file.size > SOURCE_LIMIT && file.type !== 'image/gif';
  }

  function readImage(file) {
    return new Promise(function (resolve, reject) {
      var img = new Image();
      img.onload = function () { resolve(img); };
      img.onerror = reject;
      img.src = URL.createObjectURL(file);
    });
  }

  function canvasToBlob(canvas, quality) {
    return new Promise(function (resolve) {
      canvas.toBlob(resolve, 'image/jpeg', quality);
    });
  }

  async function compressFile(file) {
    if (!canCompress(file)) return file;
    var img = await readImage(file);
    var scale = Math.min(1, MAX_EDGE / Math.max(img.width, img.height));
    var canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.round(img.width * scale));
    canvas.height = Math.max(1, Math.round(img.height * scale));
    var ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    var quality = 0.82;
    var blob = await canvasToBlob(canvas, quality);
    while (blob && blob.size > TARGET_LIMIT && quality > 0.45) {
      quality -= 0.08;
      blob = await canvasToBlob(canvas, quality);
    }
    URL.revokeObjectURL(img.src);

    if (!blob || blob.size >= file.size) return file;
    var nextName = file.name.replace(/\.[^.]+$/, '') + '.jpg';
    return new File([blob], nextName, { type: 'image/jpeg', lastModified: Date.now() });
  }

  async function compressInput(input) {
    if (!input.files || !input.files.length || typeof DataTransfer === 'undefined') return;
    var dt = new DataTransfer();
    for (var i = 0; i < input.files.length; i++) {
      dt.items.add(await compressFile(input.files[i]));
    }
    input.files = dt.files;
  }

  document.addEventListener('submit', async function (event) {
    var form = event.target;
    if (!form || !form.matches('form[data-compress-images]') || form.dataset.compressing === 'done') return;
    event.preventDefault();
    form.dataset.compressing = 'running';
    var button = form.querySelector('button[type="submit"]');
    var oldText = button ? button.textContent : '';
    if (button) {
      button.disabled = true;
      button.textContent = 'Optimizing images...';
    }
    var inputs = form.querySelectorAll('input[type="file"][accept^="image"]');
    for (var i = 0; i < inputs.length; i++) {
      await compressInput(inputs[i]);
    }
    form.dataset.compressing = 'done';
    if (button) {
      button.disabled = false;
      button.textContent = oldText;
    }
    form.submit();
  }, true);
})();
