
import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = {
    hasError: false
  };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Send these details to your configured monitoring service
    // when one is connected. Do not log tokens or sensitive data.
    console.error("Application rendering error:", error.message);
    console.error("Component stack:", info.componentStack);
  }

  handleRetry = () => {
    this.setState({ hasError: false });
  };

  render() {
    if (this.state.hasError) {
      return (
        <main className="app-error-screen">
          <div className="app-error-card">
            <div className="app-error-icon">
              <AlertTriangle size={25} />
            </div>

            <h1>Something went wrong</h1>

            <p>
              This page could not be displayed. You can retry the page
              or return to the dashboard.
            </p>

            <div className="app-error-actions">
              <button onClick={this.handleRetry}>
                <RefreshCw size={15} />
                Try again
              </button>

              <a href="/dashboard">Go to dashboard</a>
            </div>
          </div>
        </main>
      );
    }

    return this.props.children;
  }
}
