export const reportError = (error, errorInfo) => {
  if (import.meta.env.PROD) {
    // Integrate with real error tracking service here
    // e.g., send error and errorInfo to Sentry, Bugsnag, etc.
  } else {
    console.error("Captured error:", error, errorInfo);
  }
};
