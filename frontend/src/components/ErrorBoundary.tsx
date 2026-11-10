import { Component, type ReactNode, type ErrorInfo } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught error:", error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-brand-base p-6 text-slate-100">
          <h1 className="text-2xl font-bold text-brand-accent">Something went wrong</h1>
          <p className="mt-4 max-w-md rounded-lg border border-brand-edge bg-brand-surface p-4 font-mono text-sm text-red-300">
            {this.state.error?.message || "Unknown error"}
          </p>
          <button
            onClick={this.handleReset}
            className="mt-6 rounded-lg bg-brand-action px-6 py-3 font-bold text-white transition hover:bg-brand-action-dark"
          >
            Try again
          </button>
          <a href="/" className="mt-4 text-sm text-slate-400 underline hover:text-brand-accent">
            Back to home
          </a>
        </div>
      );
    }

    return this.props.children;
  }
}
