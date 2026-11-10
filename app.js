const video = document.querySelector('#camera');
const empty = document.querySelector('#empty');
const status = document.querySelector('#live-status');
const start = document.querySelector('#start');
const stop = document.querySelector('#stop');
let stream;

start.addEventListener('click', async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    status.lastChild.textContent = ' CAMERA UNAVAILABLE';
    document.querySelector('#hint').textContent = 'Open this page on localhost or HTTPS to use the camera';
    return;
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    video.srcObject = stream;
    video.style.display = 'block';
    empty.style.display = 'none';
    document.querySelector('#frame-label').style.display = 'block';
    status.classList.add('on');
    status.lastChild.textContent = ' CAMERA LIVE';
    start.disabled = true;
    stop.disabled = false;
    document.querySelector('#hint').textContent = 'Live preview · camera remains on this device';
  } catch (error) {
    const reason = error.name === 'NotAllowedError' ? 'Allow camera access in browser settings' : 'Could not access a camera on this device';
    document.querySelector('#hint').textContent = reason;
  }
});

function stopCamera() {
  stream?.getTracks().forEach(track => track.stop());
  stream = undefined;
  video.srcObject = null;
  video.style.display = 'none';
  empty.style.display = 'flex';
  document.querySelector('#frame-label').style.display = 'none';
  status.classList.remove('on');
  status.lastChild.textContent = ' CAMERA OFF';
  start.disabled = false;
  stop.disabled = true;
  document.querySelector('#hint').textContent = 'Camera stays on this device';
}

stop.addEventListener('click', stopCamera);
window.addEventListener('pagehide', stopCamera);
