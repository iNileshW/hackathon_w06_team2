import { Route, Routes, Link } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import RequestDetail from "./pages/RequestDetail";

export default function App() {
  return (
    <>
      <header className="govuk-header" data-module="govuk-header">
        <div className="govuk-header__container govuk-width-container">
          <div className="govuk-header__content">
            <Link to="/" className="govuk-header__link govuk-header__service-name">
              FOI Request Automation
            </Link>
          </div>
        </div>
      </header>

      <div className="govuk-width-container">
        <main className="govuk-main-wrapper" id="main-content" role="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/requests/:id" element={<RequestDetail />} />
          </Routes>
        </main>
      </div>

      <footer className="govuk-footer">
        <div className="govuk-width-container">
          <div className="govuk-footer__meta">
            <div className="govuk-footer__meta-item govuk-footer__meta-item--grow">
              <span className="govuk-footer__licence-description">
                Demo system &mdash; multi-agent FOI processing pipeline
              </span>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
