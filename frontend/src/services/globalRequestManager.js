class GlobalRequestManager {
  constructor() {
    this.requests = new Map();
    // Map: docId → {
    //   promise,
    //   status,
    //   response,
    //   onComplete,
    //   onError
    // }
  }

  // New request start karo
  startRequest(docId, apiFn) {
    // Agar already processing hai toh duplicate mat karo
    if (this.requests.has(docId) && this.requests.get(docId).status === "processing") {
      return this.requests.get(docId).promise;
    }

    // Recover existing callbacks if registered via setOnComplete/setOnError before starting
    const existing = this.requests.get(docId);
    const onComplete = existing?.onComplete || null;
    const onError = existing?.onError || null;

    const promise = apiFn()
      .then((response) => {
        const req = this.requests.get(docId);
        if (req) {
          req.status = "complete";
          req.response = response;
          // Callback execute karo
          if (req.onComplete) {
            req.onComplete(response);
          }
        }
        return response;
      })
      .catch((err) => {
        const req = this.requests.get(docId);
        if (req) {
          req.status = "error";
          req.error = err;
          // Callback execute karo
          if (req.onError) {
            req.onError(err);
          }
        }
        throw err;
      });

    this.requests.set(docId, {
      promise,
      status: "processing",
      response: null,
      onComplete,
      onError
    });

    return promise;
  }

  // Status check
  getStatus(docId) {
    return this.requests.get(docId)?.status || "idle";
  }

  // Response get karo
  getResponse(docId) {
    return this.requests.get(docId)?.response || null;
  }

  // Callback set karo
  setOnComplete(docId, callback) {
    if (!this.requests.has(docId)) {
      this.requests.set(docId, {
        status: "idle",
        promise: null,
        response: null,
        onComplete: callback,
        onError: null
      });
    } else {
      const req = this.requests.get(docId);
      req.onComplete = callback;
      // Agar request already complete ho chuki hai
      if (req.status === "complete" && req.response) {
        callback(req.response);
      }
    }
  }

  setOnError(docId, callback) {
    if (!this.requests.has(docId)) {
      this.requests.set(docId, {
        status: "idle",
        promise: null,
        response: null,
        onComplete: null,
        onError: callback
      });
    } else {
      const req = this.requests.get(docId);
      req.onError = callback;
      // Agar already error face kiya
      if (req.status === "error" && req.error) {
        callback(req.error);
      }
    }
  }

  // Clear request
  clear(docId) {
    this.requests.delete(docId);
  }
}

// Singleton export karo
export const requestManager = new GlobalRequestManager();
