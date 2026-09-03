import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "http://localhost:8000";

function App() {
  // ============================================================
  // EMAIL STATE
  // ============================================================

  const [emails, setEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [activeFolder, setActiveFolder] = useState("inbox");

  // ============================================================
  // AI STATE
  // ============================================================

  const [showAI, setShowAI] = useState(false);
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [trace, setTrace] = useState([]);
  const [loading, setLoading] = useState(false);

  // ============================================================
  // UI STATE
  // ============================================================

  const [emailsLoading, setEmailsLoading] = useState(false);
  const [search, setSearch] = useState("");

  // ============================================================
  // GMAIL STATE
  // ============================================================

  const [source, setSource] = useState("local");
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailEmail, setGmailEmail] = useState("");
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const profileContainerRef = useRef(null);

  // ============================================================
  // LOAD EMAILS
  // ============================================================

  const loadEmails = async (
    folder = "inbox",
    useGmail = gmailConnected
  ) => {
    setEmailsLoading(true);

    try {
      let endpoint;

      // ========================================================
      // REAL GMAIL
      // ========================================================

      if (useGmail) {
        endpoint = `${API_BASE}/api/gmail/emails?limit=50`;

        if (folder === "unread") {
          endpoint = `${API_BASE}/api/gmail/emails/unread?limit=50`;
        }

        if (folder === "important") {
          endpoint = `${API_BASE}/api/gmail/emails/important?limit=50`;
        }
      }

      // ========================================================
      // LOCAL DEMO
      // ========================================================

      else {
        endpoint = `${API_BASE}/api/emails?limit=50`;

        if (folder === "unread") {
          endpoint = `${API_BASE}/api/emails/unread?limit=50`;
        }

        if (folder === "important") {
          endpoint = `${API_BASE}/api/emails/important?limit=50`;
        }
      }

      console.log(
        `Loading ${useGmail ? "Gmail" : "local"} emails from:`,
        endpoint
      );

      const res = await fetch(endpoint, {
        credentials: "omit", // Using omit just in case backend doesn't support CORS credentials, since token is stored in backend
      });

      if (!res.ok) {
        throw new Error(
          `Failed to load emails: ${res.status}`
        );
      }

      const data = await res.json();

      // --------------------------------------------------------
      // Backend may return:
      //   []
      //   { emails: [] }
      //   { data: [] }
      // --------------------------------------------------------

      let emailList = [];

      if (Array.isArray(data)) {
        emailList = data;
      } else if (data && Array.isArray(data.emails)) {
        emailList = data.emails;
      } else if (data && Array.isArray(data.data)) {
        emailList = data.data;
      } else if (data && Array.isArray(data.messages)) {
        emailList = data.messages;
      } else if (data && Array.isArray(data.results)) {
        emailList = data.results;
      } else if (data && Array.isArray(data.items)) {
        emailList = data.items;
      }

      console.log(
        `${useGmail ? "Gmail" : "Local"} emails received:`,
        emailList.length
      );

      setEmails(emailList);
      setSelectedEmail(null);
    } catch (error) {
      console.error(
        `${useGmail ? "Gmail" : "Local"} email loading error:`,
        error
      );

      /*
       * IMPORTANT:
       *
       * If Gmail is selected and Gmail loading fails,
       * do NOT replace Gmail data with local demo data.
       *
       * This prevents the confusing situation where Gmail
       * says connected but local demo emails are displayed.
       */

      setEmails([]);
      setSelectedEmail(null);
    } finally {
      setEmailsLoading(false);
    }
  };

  // ============================================================
  // CHECK GMAIL STATUS
  // ============================================================

  const checkGmailStatus = async () => {
    try {
      console.log("Checking Gmail connection...");

      const res = await fetch(
        `${API_BASE}/api/gmail/status`,
        {
          cache: "no-store",
          credentials: "omit"
        }
      );

      if (!res.ok) {
        console.error(
          "Gmail status request failed:",
          res.status
        );

        setGmailConnected(false);
        setGmailEmail("");

        return false;
      }

      const data = await res.json();

      console.log("Gmail status response:", data);

      const connected = data === true || Boolean(
        data?.authenticated ||
        data?.connected ||
        data?.is_authenticated ||
        data?.status === "connected" ||
        data?.status === "authenticated"
      );

      setGmailConnected(connected);

      // ========================================================
      // CONNECTED
      // ========================================================

      if (connected) {
        setSource("gmail");

        // ------------------------------------------------------
        // Load Gmail profile
        // ------------------------------------------------------

        try {
          const profileRes = await fetch(
            `${API_BASE}/api/gmail/profile`,
            {
              cache: "no-store",
              credentials: "omit"
            }
          );

          if (profileRes.ok) {
            const profile = await profileRes.json();

            console.log(
              "Gmail profile:",
              profile
            );

            const emailAddress =
              profile.email ||
              profile.emailAddress ||
              profile.address ||
              "";

            setGmailEmail(emailAddress);
          } else {
            console.warn(
              "Gmail profile request failed:",
              profileRes.status
            );

            setGmailEmail("");
          }
        } catch (profileError) {
          console.error(
            "Unable to load Gmail profile:",
            profileError
          );

          setGmailEmail("");
        }

        return true;
      }

      // ========================================================
      // NOT CONNECTED
      // ========================================================

      setSource("local");
      setGmailEmail("");

      return false;
    } catch (error) {
      console.error(
        "Gmail status error:",
        error
      );

      setGmailConnected(false);
      setGmailEmail("");
      setSource("local");

      return false;
    }
  };

  // ============================================================
  // INITIAL APP LOAD
  // ============================================================

  useEffect(() => {
    const initializeApp = async () => {
      /*
       * After Google OAuth your backend redirects to something
       * like:
       *
       * http://localhost:5173/?gmail=connected
       *
       * We detect that here.
       */

      const params = new URLSearchParams(
        window.location.search
      );

      const gmailCallback =
        params.get("gmail");

      if (gmailCallback === "connected") {
        console.log(
          "Gmail OAuth callback detected."
        );

        /*
         * Remove ?gmail=connected from the address bar
         * without reloading the application.
         */

        window.history.replaceState(
          {},
          document.title,
          window.location.pathname
        );
      }

      // --------------------------------------------------------
      // Check backend Gmail authentication
      // --------------------------------------------------------

      const connected =
        await checkGmailStatus();

      // --------------------------------------------------------
      // Load appropriate emails
      // --------------------------------------------------------

      if (connected) {
        setSource("gmail");

        await loadEmails(
          "inbox",
          true
        );
      } else {
        setSource("local");

        await loadEmails(
          "inbox",
          false
        );
      }
    };

    initializeApp();
  }, []);

  // ============================================================
  // PROFILE MENU - CLOSE WHEN CLICKING OUTSIDE
  // ============================================================

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        profileContainerRef.current &&
        !profileContainerRef.current.contains(
          event.target
        )
      ) {
        setShowProfileMenu(false);
      }
    };

    document.addEventListener(
      "mousedown",
      handleClickOutside
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClickOutside
      );
    };
  }, []);

  // ============================================================
  // CHANGE FOLDER
  // ============================================================

  const changeFolder = async (folder) => {
    setActiveFolder(folder);
    setSelectedEmail(null);
    setSearch("");

    await loadEmails(
      folder,
      gmailConnected
    );
  };

  // ============================================================
  // CONNECT GMAIL
  // ============================================================

  const connectGmail = () => {
    console.log(
      "Starting Google OAuth..."
    );

    setShowProfileMenu(false);

    /*
     * Navigate to backend OAuth endpoint.
     *
     * The backend should:
     * 1. Redirect to Google
     * 2. Handle callback
     * 3. Save token.json
     * 4. Redirect back to:
     *
     * http://localhost:5173/?gmail=connected
     */

    window.location.href =
      `${API_BASE}/api/auth/google`;
  };

  // ============================================================
  // DISCONNECT GMAIL
  // ============================================================

  const disconnectGmail = async () => {
    try {
      console.log(
        "Disconnecting Gmail..."
      );

      const res = await fetch(
        `${API_BASE}/api/gmail/logout`,
        {
          method: "POST",
          credentials: "omit"
        }
      );

      if (!res.ok) {
        throw new Error(
          `Logout failed: ${res.status}`
        );
      }

      console.log(
        "Gmail disconnected successfully."
      );

      // ========================================================
      // CLEAR GMAIL STATE IMMEDIATELY
      // ========================================================

      setGmailConnected(false);
      setGmailEmail("");
      setShowProfileMenu(false);

      // ========================================================
      // SWITCH BACK TO LOCAL DEMO
      // ========================================================

      setSource("local");
      setActiveFolder("inbox");
      setSelectedEmail(null);
      setSearch("");

      // ========================================================
      // REMOVE REAL GMAIL EMAILS IMMEDIATELY
      // ========================================================

      setEmails([]);

      // ========================================================
      // LOAD LOCAL DEMO EMAILS
      // ========================================================

      await loadEmails(
        "inbox",
        false
      );
    } catch (error) {
      console.error(
        "Logout error:",
        error
      );

      alert(
        "Unable to disconnect Gmail. Please make sure the backend is running."
      );
    }
  };

  // ============================================================
  // SELECT EMAIL
  // ============================================================

  const selectEmail = async (email) => {
    setSelectedEmail(email);

    // ----------------------------------------------------------
    // Only local demo emails are marked read here.
    // Gmail read/unread state should be handled by Gmail API.
    // ----------------------------------------------------------

    if (
      !email.read &&
      source === "local"
    ) {
      try {
        await fetch(
          `${API_BASE}/api/emails/${email.id}/read`,
          {
            method: "PATCH",
            credentials: "omit"
          }
        );

        setEmails((current) =>
          current.map((item) =>
            item.id === email.id
              ? {
                ...item,
                read: true,
              }
              : item
          )
        );

        setSelectedEmail({
          ...email,
          read: true,
        });
      } catch (error) {
        console.error(
          "Unable to mark email as read:",
          error
        );
      }
    }
  };

  // ============================================================
  // SEARCH
  // ============================================================

  const filteredEmails = emails.filter(
    (email) => {
      const text =
        search
          .toLowerCase()
          .trim();

      if (!text) {
        return true;
      }

      return (
        email.sender
          ?.toLowerCase()
          .includes(text) ||
        email.subject
          ?.toLowerCase()
          .includes(text) ||
        email.body
          ?.toLowerCase()
          .includes(text) ||
        email.snippet
          ?.toLowerCase()
          .includes(text)
      );
    }
  );

  // ============================================================
  // OPEN / CLOSE AI PANEL
  // ============================================================

  const toggleAI = () => {
    setShowAI(
      (current) => !current
    );
  };

  // ============================================================
  // ASK AI
  // ============================================================

  const askAssistant = async () => {
    if (!message.trim()) {
      return;
    }

    setLoading(true);
    setResponse("");
    setTrace([]);

    try {
      const res = await fetch(
        `${API_BASE}/api/email-agent`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          credentials: "omit",
          body: JSON.stringify({
            request: message,
            source: source,
          }),
        }
      );

      if (!res.ok) {
        throw new Error(
          `Server error: ${res.status}`
        );
      }

      const data =
        await res.json();

      setResponse(
        data.response ||
        data.answer ||
        "No response received."
      );

      setTrace(
        data.trace || []
      );
    } catch (error) {
      console.error(
        "AI error:",
        error
      );

      setResponse(
        "Unable to connect to the AI backend. Make sure FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // KEYBOARD
  // ============================================================

  const handleKeyDown = (
    event
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      askAssistant();
    }
  };

  // ============================================================
  // FOLDER TITLE
  // ============================================================

  const getFolderTitle = () => {
    if (
      activeFolder ===
      "unread"
    ) {
      return "Unread";
    }

    if (
      activeFolder ===
      "important"
    ) {
      return "Important";
    }

    return "Inbox";
  };

  // ============================================================
  // DRAFT AI REPLY
  // ============================================================

  const draftReply = () => {
    if (!selectedEmail) {
      return;
    }

    setMessage(
      `Draft a reply to ${selectedEmail.sender} regarding "${selectedEmail.subject}".`
    );

    setShowAI(true);

    setTimeout(() => {
      document
        .querySelector(
          ".ai-input"
        )
        ?.focus();
    }, 150);
  };

  // ============================================================
  // COMPOSE / AI HELP
  // ============================================================

  const openAIWithMessage = (
    text
  ) => {
    setMessage(text);
    setShowAI(true);

    setTimeout(() => {
      document
        .querySelector(
          ".ai-input"
        )
        ?.focus();
    }, 150);
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div
      className={`gmail-app ${showAI ? "ai-open" : ""
        }`}
    >
      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="sidebar">

        {/* LOGO */}

        <div className="gmail-logo">
          <div className="gmail-logo-icon">
            M
          </div>

          <span>
            Email AI
          </span>
        </div>

        {/* COMPOSE (Removed) */}

        {/* NAVIGATION */}

        <nav className="sidebar-nav">

          {/* INBOX */}

          <button
            className={`nav-item ${activeFolder ===
                "inbox"
                ? "active"
                : ""
              }`}
            onClick={() =>
              changeFolder(
                "inbox"
              )
            }
          >
            <span className="nav-icon">
              ▣
            </span>

            <span>
              Inbox
            </span>

            <span className="nav-count">
              {emails.length || ""}
            </span>
          </button>

          {/* IMPORTANT */}

          <button
            className={`nav-item ${activeFolder ===
                "important"
                ? "active"
                : ""
              }`}
            onClick={() =>
              changeFolder(
                "important"
              )
            }
          >
            <span className="nav-icon">
              ★
            </span>

            <span>
              Important
            </span>
          </button>

          {/* UNREAD */}

          <button
            className={`nav-item ${activeFolder ===
                "unread"
                ? "active"
                : ""
              }`}
            onClick={() =>
              changeFolder(
                "unread"
              )
            }
          >
            <span className="nav-icon">
              ●
            </span>

            <span>
              Unread
            </span>
          </button>
        </nav>

        {/* AI NAVIGATION */}

        <div className="sidebar-section">
          <div className="sidebar-section-title">
            AI Assistant
          </div>

          <button
            className={`nav-item ai-nav ${showAI
                ? "active"
                : ""
              }`}
            onClick={
              toggleAI
            }
          >
            <span className="nav-icon">
              🤖
            </span>

            <span>
              {showAI
                ? "Close AI"
                : "Ask AI"}
            </span>
          </button>
        </div>

        {/* GMAIL CONNECTION */}

        <div className="sidebar-bottom">
          <div className="gmail-connection">

            <div>
              <strong>
                Gmail
              </strong>

              <small>
                {gmailConnected
                  ? "Connected"
                  : "Not connected"}
              </small>
            </div>

            {!gmailConnected && (
              <button
                className="connect-button"
                onClick={
                  connectGmail
                }
              >
                Connect
              </button>
            )}

            {gmailConnected && (
              <span className="connected-dot">
                ●
              </span>
            )}
          </div>
        </div>
      </aside>

      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="main">

        {/* ====================================================
            TOP BAR
        ==================================================== */}

        <header className="topbar">

          <div className="search-box">

            <span>
              ⌕
            </span>

            <input
              type="text"
              placeholder="Search mail"
              value={search}
              onChange={(e) =>
                setSearch(
                  e.target.value
                )
              }
            />

            {search && (
              <button
                className="clear-search"
                onClick={() =>
                  setSearch("")
                }
                title="Clear search"
              >
                ×
              </button>
            )}
          </div>

          <div className="topbar-right">

            {/* CONNECTION STATUS */}

            <span
              className={
                gmailConnected
                  ? "connection-status connected"
                  : "connection-status"
              }
              title={
                gmailConnected
                  ? "Gmail connected"
                  : "Gmail not connected"
              }
            >
              ●
            </span>

            {/* PROFILE */}

            <div
              className="profile-container"
              ref={
                profileContainerRef
              }
            >
              <button
                className="profile"
                onClick={() =>
                  setShowProfileMenu(
                    (current) =>
                      !current
                  )
                }
                title="Account"
              >
                {gmailEmail
                  ? gmailEmail
                    .charAt(
                      0
                    )
                    .toUpperCase()
                  : "U"}
              </button>

              {showProfileMenu && (
                <div className="profile-menu">

                  {/* PROFILE HEADER */}

                  <div className="profile-menu-header">

                    <div className="profile-menu-avatar">
                      {gmailEmail
                        ? gmailEmail
                          .charAt(
                            0
                          )
                          .toUpperCase()
                        : "U"}
                    </div>

                    <div className="profile-menu-info">

                      <strong>
                        {gmailConnected
                          ? "Gmail Account"
                          : "Local Demo"}
                      </strong>

                      <span>
                        {gmailConnected
                          ? gmailEmail ||
                          "Connected"
                          : "Not connected"}
                      </span>

                    </div>
                  </div>

                  <div className="profile-menu-divider" />

                  {/* CONNECT / DISCONNECT */}

                  {gmailConnected ? (
                    <button
                      className="profile-menu-item logout"
                      onClick={
                        disconnectGmail
                      }
                    >
                      <span>
                        ↪
                      </span>

                      Disconnect Gmail
                    </button>
                  ) : (
                    <button
                      className="profile-menu-item"
                      onClick={
                        connectGmail
                      }
                    >
                      <span>
                        ＋
                      </span>

                      Connect Gmail
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>

        {/* ====================================================
            MAIN CONTENT (Row layout for AI panel)
        ==================================================== */}

        <div className="main-content" style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>

          {/* ====================================================
              EMAIL AREA
          ==================================================== */}

          <section className="email-area">

          {/* ==================================================
              EMAIL LIST
          ================================================== */}

          <div className="email-list-panel">

            <div className="list-header">

              <div>
                <h1>
                  {getFolderTitle()}
                </h1>

                <span>
                  {filteredEmails.length} emails
                </span>
              </div>

              <button
                className="refresh-button"
                onClick={() =>
                  loadEmails(
                    activeFolder,
                    gmailConnected
                  )
                }
                title="Refresh emails"
              >
                ↻
              </button>
            </div>

            {/* LOADING */}

            {emailsLoading ? (
              <div className="empty-state">

                <div className="spinner" />

                <p>
                  Loading emails...
                </p>
              </div>
            ) : filteredEmails.length ===
              0 ? (
              /* EMPTY */

              <div className="empty-state">

                <div className="empty-icon">
                  ✉
                </div>

                <h3>
                  {gmailConnected
                    ? "No Gmail emails found"
                    : "No emails found"}
                </h3>

                <p>
                  {gmailConnected
                    ? "Your Gmail inbox is empty or the Gmail API could not return any messages."
                    : "There are no emails in this folder."}
                </p>
              </div>
            ) : (
              /* EMAIL LIST */

              <div className="email-list">

                {filteredEmails.map(
                  (email) => (
                    <button
                      key={
                        email.id
                      }
                      className={`email-row ${!email.read
                          ? "unread-email"
                          : ""
                        } ${selectedEmail?.id ===
                          email.id
                          ? "selected-email"
                          : ""
                        }`}
                      onClick={() =>
                        selectEmail(
                          email
                        )
                      }
                    >

                      <div className="email-star">
                        {email.priority ===
                          "High"
                          ? "★"
                          : "☆"}
                      </div>

                      <div className="email-info">

                        <div className="email-top">

                          <strong>
                            {email.sender ||
                              email.from ||
                              "Unknown sender"}
                          </strong>

                          <span>
                            {email.timestamp
                              ? new Date(
                                email.timestamp
                              ).toLocaleDateString()
                              : email.date
                                ? new Date(
                                  email.date
                                ).toLocaleDateString()
                                : ""}
                          </span>
                        </div>

                        <div className="email-subject">

                          {email.subject ||
                            "(No subject)"}

                          {!email.read && (
                            <span className="unread-badge">
                              Unread
                            </span>
                          )}

                          {email.priority ===
                            "High" && (
                              <span className="priority-badge">
                                High
                              </span>
                            )}
                        </div>

                        <div className="email-preview">
                          {email.body ||
                            email.snippet ||
                            ""}
                        </div>
                      </div>
                    </button>
                  )
                )}
              </div>
            )}
          </div>

          {/* ==================================================
              READING PANEL
          ================================================== */}

          <div className="reading-panel">

            {!selectedEmail ? (
              <div className="reading-empty">

                <div className="large-mail-icon">
                  ✉
                </div>

                <h2>
                  Select an email
                </h2>

                <p>
                  Click an email to read its
                  contents.
                </p>
              </div>
            ) : (
              <article className="email-reader">

                <div className="reader-header">

                  <div>

                    <h2>
                      {selectedEmail.subject ||
                        "(No subject)"}
                    </h2>

                    <div className="reader-sender">

                      <div className="sender-avatar">
                        {(
                          selectedEmail.sender ||
                          selectedEmail.from ||
                          "U"
                        )
                          ?.charAt(0)
                          ?.toUpperCase()}
                      </div>

                      <div>

                        <strong>
                          {selectedEmail.sender ||
                            selectedEmail.from ||
                            "Unknown sender"}
                        </strong>

                        <span>
                          to{" "}
                          {selectedEmail.recipient ||
                            selectedEmail.to ||
                            "me"}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="reader-actions">

                    {selectedEmail.priority ===
                      "High" && (
                        <span className="priority-badge">
                          High Priority
                        </span>
                      )}
                  </div>
                </div>

                <div 
                  className="email-body"
                  dangerouslySetInnerHTML={{
                    __html: selectedEmail.body || selectedEmail.snippet || "No email content available."
                  }}
                />

                {selectedEmail.requires_reply && (
                  <button
                    className="reply-button"
                    onClick={
                      draftReply
                    }
                  >
                    ↩ Draft AI Reply
                  </button>
                )}
              </article>
            )}
          </div>
        </section>

        {/* ====================================================
            AI ASSISTANT DRAWER
        ==================================================== */}

        {showAI && (
          <section className="ai-panel">

            {/* AI HEADER */}

            <div className="ai-header">

              <div className="ai-title">

                <div className="ai-icon">
                  🤖
                </div>

                <div>
                  <h2>
                    AI Email Assistant
                  </h2>

                  <p>
                    Search, summarize and
                    understand your emails
                  </p>
                </div>
              </div>

              <div className="ai-header-actions">

                {/* SOURCE TOGGLE */}

                <div className="source-toggle">

                  <button
                    className={
                      source ===
                        "local"
                        ? "source-active"
                        : ""
                    }
                    onClick={async () => {
                      setSource(
                        "local"
                      );

                      setSelectedEmail(
                        null
                      );

                      await loadEmails(
                        activeFolder,
                        false
                      );
                    }}
                  >
                    Local Demo
                  </button>

                  <button
                    className={
                      source ===
                        "gmail"
                        ? "source-active"
                        : ""
                    }
                    onClick={async () => {

                      if (
                        !gmailConnected
                      ) {
                        alert(
                          "Connect Gmail first."
                        );
                        return;
                      }

                      setSource(
                        "gmail"
                      );

                      setSelectedEmail(
                        null
                      );

                      await loadEmails(
                        activeFolder,
                        true
                      );
                    }}
                  >
                    Real Gmail
                  </button>
                </div>

                {/* CLOSE BUTTON */}

                <button
                  className="ai-close-button"
                  onClick={
                    toggleAI
                  }
                  title="Close AI Assistant"
                >
                  ×
                </button>
              </div>
            </div>

            {/* AI CONTENT */}

            <div className="ai-content">

              <div className="ai-chat">

                <select
                  className="ai-input"
                  value={message}
                  onChange={(e) =>
                    setMessage(
                      e.target.value
                    )
                  }
                  onKeyDown={
                    handleKeyDown
                  }
                >
                  <option value="" disabled>Select a prompt...</option>
                  <option value="Summarize all my emails">Summarize all my emails</option>
                  <option value="Find my unread high priority emails">Find my unread high priority emails</option>
                  <option value="Do I have any urgent emails?">Do I have any urgent emails?</option>
                  <option value="Summarize emails from my boss">Summarize emails from my boss</option>
                  <option value="What are my action items for today?">What are my action items for today?</option>
                </select>

                <button
                  className="ask-button"
                  onClick={
                    askAssistant
                  }
                  disabled={
                    loading ||
                    !message.trim()
                  }
                >
                  {loading
                    ? "Thinking..."
                    : "Ask AI →"}
                </button>
              </div>

              {/* AI RESPONSE */}

              {response && (
                <div className="ai-response">

                  <div className="ai-section-title">

                    <span>
                      🤖
                    </span>

                    AI Response
                  </div>

                  <div className="response-content">
                    {response}
                  </div>
                </div>
              )}

              {/* TRACE */}

              {trace.length >
                0 && (
                  <div className="trace-section">

                    <div className="ai-section-title">

                      <span>
                        ⚙
                      </span>

                      Agent Activity
                    </div>

                    <div className="trace-list">

                      {trace.map(
                        (
                          item,
                          index
                        ) => (
                          <div
                            className="trace-item"
                            key={
                              index
                            }
                          >

                            <div
                              className={
                                item.type ===
                                  "tool"
                                  ? "trace-icon tool"
                                  : "trace-icon"
                              }
                            >
                              {item.type ===
                                "tool"
                                ? "🔍"
                                : "✓"}
                            </div>

                            <div>

                              <strong>
                                {item.message ||
                                  item.step ||
                                  item.type}
                              </strong>

                              {item.detail && (
                                <span>
                                  {
                                    item.detail
                                  }
                                </span>
                              )}
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
            </div>
          </section>
        )}

        </div>
      </main>
    </div>
  );
}

export default App;