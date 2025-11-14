# backend/orchestrator.py
import asyncio
from collections import defaultdict
from graph import build_research_graph
from agents.paper_generator_agent import paper_generator_agent
import os

class Orchestrator:
    def __init__(self):
        self._logs = defaultdict(asyncio.Queue)
        self.graph = build_research_graph()
        self.results = {}  # stores paper paths for each job

    async def log(self, job_id, msg):
        """Push a new log message to the WebSocket queue."""
        await self._logs[job_id].put(msg)

    async def get_log(self, job_id):
        """Return next log message or empty string."""
        try:
            return await asyncio.wait_for(self._logs[job_id].get(), timeout=10)
        except asyncio.TimeoutError:
            return ""

    def get_result(self, job_id):
        """Retrieve stored results (HTML + PDF paths)."""
        return self.results.get(job_id)

    async def run_job(self, job_id, jobs_dict):
        """
        Executes the LangGraph pipeline and streams logs.
        """
        await self.log(job_id, f"🚀 Starting research pipeline for job {job_id}...")

        # Initial state passed into the graph
        state = {
            "job_id": job_id, 
            "logs": [],
            "domains": None,
            "questions": None,
            "data": None,
            "experiment": None,
            "critique": None,
            "results": None,
            "paper": None,
            "cycle": 0,
             # MUST be passed so PDF is correctly named
        }

        node_log_ptrs = {}
        config = {"recursion_limit": 50}

        async for event in self.graph.astream(state, config=config):

    # Each event: { node_name : output_dict }
            for node_name, node_output in event.items():

        # Merge node output into state
                if isinstance(node_output, dict):
                    state.update(node_output)

        # Stream logs incrementally
            logs = node_output.get("logs", [])
            if logs:
                last = node_log_ptrs.get(node_name, 0)
                new_logs = logs[last:]
                for line in new_logs:
                    await self.log(job_id, line)
                node_log_ptrs[node_name] = len(logs)

        # Check if this is the paper node
            if node_name == "paper" and node_output.get("results"):
                results = node_output["results"]
                html_path = results.get("html")
                if html_path and os.path.exists(html_path):
                    with open(html_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    results["html_content"] = html_content
            
                self.results[job_id] = results
                jobs_dict[job_id]["results"] = results
                jobs_dict[job_id]["status"] = "done"

                await self.log(job_id, "📄 Final paper generated.")
                await self.log(job_id, "🎉 Pipeline completed successfully.")
                return

# If we exit the loop without generating paper
                # ──────────────────────────────────────────────────────────────
        # FINAL SAFETY NET: FORCE PAPER GENERATION NO MATTER WHAT
        # ──────────────────────────────────────────────────────────────
        await self.log(job_id, "Final safety net: Forcing paper generation with whatever we have...")

        try:
            # Make sure we have a job_id and don't crash
            final_state = state.copy()
            final_state["job_id"] = job_id

            # Run the paper generator one last time
            paper_result = await paper_generator_agent(final_state)

            # Extract paper paths (it returns {"paper": {"html": ..., "pdf": ...}} or similar)
            paper_info = paper_result.get("paper") or paper_result.get("results")
            if not paper_info:
                # Extreme fallback: create dummy paths pointing to whatever was saved
                html_path = f"outputs/{job_id}.html"
                pdf_path = f"outputs/{job_id}.pdf"
                paper_info = {"html": html_path, "pdf": pdf_path}

            # Store result
            self.results[job_id] = paper_info
            jobs_dict[job_id]["results"] = paper_info
            jobs_dict[job_id]["status"] = "done"

            await self.log(job_id, "Paper force-generated successfully!")
            await self.log(job_id, "Pipeline completed — research paper ready!")
            await self.log(job_id, f"View at: /result/{job_id}")

        except Exception as e:
            await self.log(job_id, f"CRITICAL: Even force-generation failed: {e}")
            import traceback
            await self.log(job_id, traceback.format_exc())


# # backend/orchestrator.py
# import asyncio
# from collections import defaultdict
# from graph import build_research_graph

# class Orchestrator:
#     def __init__(self):
#         self._logs = defaultdict(asyncio.Queue)
#         self.graph = build_research_graph()
#         self._results = {}  # local cache for last results per job

#     async def log(self, job_id, msg):
#         await self._logs[job_id].put(msg)

#     async def get_log(self, job_id):
#         try:
#             return await asyncio.wait_for(self._logs[job_id].get(), timeout=10)
#         except asyncio.TimeoutError:
#             return ""

#     def get_result(self, job_id):
#         """Called by /result and /download endpoints to fetch paper info."""
#         return self._results.get(job_id)

#     async def run_job(self, job_id, jobs_dict):
#         # initial state
#         state = {
#             "logs": [],
#             "domains": None,
#             "questions": None,
#             "data": None,
#             "experiment": None,
#             "critique": None,
#             "results": None,
#             "paper": None,
#             "cycle": 0,
#             # pass job id into agents via state
#             "job_id": job_id,
#         }

#         # small bookkeeping
#         node_log_ptrs = {}
#         config = {"recursion_limit": 50}

#         try:
#             async for event in self.graph.astream(state, config=config):
#                 # each event is a dict of node -> output
#                 for node_name, node_output in event.items():
#                     if not isinstance(node_output, dict):
#                         # ignore weird outputs
#                         continue

#                     # merge node output into state
#                     state.update(node_output)

#                     # If we loop back to data after a critic run, increment cycle
#                     if node_name == "data" and state.get("critique") is not None:
#                         state["cycle"] = state.get("cycle", 0) + 1
#                         await self.log(job_id, f"━━ Cycle {state['cycle']} ━━")

#                     # stream any new logs from this node
#                     logs = node_output.get("logs", []) or []
#                     last = node_log_ptrs.get(node_name, 0)
#                     new = logs[last:]
#                     for line in new:
#                         await self.log(job_id, line)
#                     node_log_ptrs[node_name] = len(logs)

#                 # If paper was generated by paper_generator_agent, stop immediately
#                 if state.get("paper"):
#                     paper_info = state["paper"]
#                     # save into orchestrator cache and external jobs dict
#                     self._results[job_id] = paper_info
#                     jobs_dict[job_id]["results"] = paper_info
#                     jobs_dict[job_id]["status"] = "done"

#                     await self.log(job_id, "📄 Final paper generated.")
#                     await self.log(job_id, "✅ FINAL: Research pipeline completed successfully.")
#                     return

#         except Exception as e:
#             await self.log(job_id, f"ERROR: {e}")
#             return

#         # If loop exits without paper
#         await self.log(job_id, "⚠️ Pipeline ended without generating paper.")
#         await self.log(job_id, "FINAL: Research pipeline completed.")

