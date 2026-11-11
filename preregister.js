const form = document.querySelector("#preregister-form");
const button = document.querySelector("#submit-button");
const buttonCopy = button.querySelector(".button-copy");
const status = document.querySelector("#form-status");
const emailInput = document.querySelector("#email");
const accessKey = process.env.NEXT_PUBLIC_WEB3FORMS_KEY || 'YOUR_ACCESS_KEY';

function showStatus(message, kind = "error") {
  status.textContent = message;
  status.className = `form-status ${kind}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  status.textContent = "";
  status.className = "form-status";

  if (!emailInput.checkValidity()) {
    emailInput.reportValidity();
    return;
  }
  if (!accessKey || accessKey === "YOUR_ACCESS_KEY") {
    showStatus("Die Anmeldung ist noch nicht eingerichtet. Bitte versuche es später erneut.");
    return;
  }

  const originalButtonCopy = buttonCopy.textContent;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  buttonCopy.innerHTML = '<span class="spinner" aria-hidden="true"></span> Wird gesendet …';

  try {
    const payload = Object.fromEntries(new FormData(form).entries());
    payload.access_key = accessKey;
    payload.subject = "Neue Voranmeldung · Gut ankommen";
    payload.from_name = "Gut ankommen Early Access";

    const response = await fetch("https://api.web3forms.com/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.message || "Die Anmeldung konnte nicht gesendet werden.");
    }

    form.reset();
    showStatus("Vielen Dank! Du bist auf der Warteliste.", "success");
  } catch (error) {
    showStatus("Das hat leider nicht geklappt. Bitte versuche es noch einmal.");
    console.error("Web3Forms submission failed:", error);
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    buttonCopy.textContent = originalButtonCopy;
  }
});
