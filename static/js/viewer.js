// Built-in Sovereign Ledger PDF Viewer Engine
let currentPdfDocId = null;
let currentPdfPage = 1;
let totalPdfPages = 1;

function openPdfViewer(docId, docName, targetPage = 1, highlightTitle = "", highlightSnippet = "") {
  currentPdfDocId = docId;
  currentPdfPage = targetPage;

  const modal = document.getElementById("pdfViewerModal");
  const titleEl = document.getElementById("viewerDocTitle");
  const highlightEl = document.getElementById("viewerHighlightBanner");
  const highlightTextEl = document.getElementById("viewerHighlightText");
  const frame = document.getElementById("pdfViewerFrame");
  const pageIndicator = document.getElementById("viewerPageIndicator");

  titleEl.innerText = docName || "Document Viewer";

  if (highlightTitle) {
    highlightEl.classList.remove("hidden");
    highlightTextEl.innerHTML = `<strong>${highlightTitle}</strong>: ${highlightSnippet} (Page ${targetPage})`;
  } else {
    highlightEl.classList.add("hidden");
  }

  // Fetch short-lived signed access token for the document iframe
  fetch(`/api/documents/${docId}/signed-url`, {
    headers: { "Authorization": `Bearer ${AppState.sessionToken || ""}` }
  })
  .then(res => res.json())
  .then(data => {
    const signedUrl = data.signed_url || `/api/documents/${docId}/file`;
    frame.src = `${signedUrl}#page=${targetPage}&toolbar=1&navpanes=1`;
  })
  .catch(err => {
    console.error("Failed to acquire signed document URL:", err);
    frame.src = `/api/documents/${docId}/file#page=${targetPage}&toolbar=1&navpanes=1`;
  });

  pageIndicator.innerText = `Target: Page ${targetPage}`;
  modal.classList.remove("hidden");
  document.body.style.overflow = "hidden";
}

function closePdfViewer() {
  const modal = document.getElementById("pdfViewerModal");
  const frame = document.getElementById("pdfViewerFrame");
  frame.src = "about:blank";
  modal.classList.add("hidden");
  document.body.style.overflow = "auto";
}

function jumpViewerPage(pageNum) {
  if (!currentPdfDocId) return;
  currentPdfPage = pageNum;
  const frame = document.getElementById("pdfViewerFrame");
  frame.src = `/api/documents/${currentPdfDocId}/file#page=${pageNum}&toolbar=1`;
  document.getElementById("viewerPageIndicator").innerText = `Page ${pageNum}`;
}
