/* Site settings read by js/site.js.
   LEADS_URL: the /exec URL of the Apps Script web app in apps-script/ (see apps-script/DEPLOY.md).
   While it is empty, every form shows its success state and opens a pre-filled email to CONTACT_EMAIL instead,
   so no enquiry is lost. If a post to LEADS_URL fails, the same email fallback opens. */
window.SITE_CONFIG = {
  LEADS_URL: "",
  CONTACT_EMAIL: "contactarenax@gmail.com"
};
