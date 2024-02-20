
  var timer;
  var expiryTime = new Date('{{ expiry_time|date:"c" }}');  // Parse the Django datetime in JavaScript

  // Start the timer automatically when the page loads
  window.onload = function() {
    startTimer();
  };

  function startTimer() {
    timer = setInterval(function() {
      var currentTime = new Date();
      var remainingTime = Math.max(0, Math.floor((expiryTime - currentTime) / 1000));

      displayTime(remainingTime);

      if (remainingTime === 0) {
        clearInterval(timer);
        document.getElementById('timer').style.display = 'none';
        document.getElementById('timerButton').style.display = 'block';
      }
    }, 1000);
  }

  function displayTime(seconds) {
    var minutes = Math.floor(seconds / 60);
    var remainingSeconds = seconds % 60;

    document.getElementById('timer').innerText = `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
  }
