import { useEffect, useState } from "react";

import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});


function App() {
  const [backendStatus, setBackendStatus] = useState("Checking...");


  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await api.get("/health");

        setBackendStatus(response.data.status);
      } catch (error) {
        console.error(error);

        setBackendStatus("unavailable");
      }
    };


    checkBackend();
  }, []);


  return (
    <div className="app">

      <header className="header">

        <h1>
          AI Recruitment & Candidate Matching Platform
        </h1>

        <p>
          AI-powered recruitment and candidate analysis
        </p>

      </header>


      <main className="container">

        <section className="status-card">

          <h2>
            System Status
          </h2>

          <p>
            Backend:
            {" "}
            <strong>
              {backendStatus}
            </strong>
          </p>

        </section>


        <section className="card">

          <h2>
            Job Description
          </h2>

          <p>
            Create or upload a Job Description.
          </p>

          <button>
            Create Job
          </button>

        </section>


        <section className="card">

          <h2>
            Candidates
          </h2>

          <p>
            Upload candidate resumes for AI analysis.
          </p>

          <button>
            Upload Resumes
          </button>

        </section>

      </main>

    </div>
  );
}


export default App;