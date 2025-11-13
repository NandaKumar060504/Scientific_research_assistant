# backend/orchestrator.py
import asyncio
from collections import defaultdict

class Orchestrator:
    def __init__(self):
        self._logs = defaultdict(asyncio.Queue)
        self.max_cycles = 5

    async def log(self, job_id, message):
        await self._logs[job_id].put(message)

    async def get_log(self, job_id, timeout=10):
        try:
            message = await asyncio.wait_for(self._logs[job_id].get(), timeout=timeout)
            return message
        except asyncio.TimeoutError:
            return ""

    async def run_job(self, job_id):
        await self.log(job_id, "Job started: orchestrator online")
        await asyncio.sleep(0.5)
        # Domain Scout stub
        await self.log(job_id, "DomainScout: searching for emerging domains...")
        await asyncio.sleep(1.0)
        domains = [{"name": "Quantum-inspired GNNs", "score": 0.82},
                   {"name": "AI-driven materials discovery", "score": 0.74}]
        await self.log(job_id, f"DomainScout -> {domains}")

        # Question Generator stub
        await self.log(job_id, "QuestionGenerator: producing candidate questions...")
        await asyncio.sleep(0.8)
        questions = [{"q":"Does quantum-inspired message passing improve GNN generalization?", "novelty":0.7}]
        await self.log(job_id, f"QuestionGenerator -> {questions}")

        # Data Alchemist stub
        await self.log(job_id, "DataAlchemist: acquiring & cleaning sample data...")
        await asyncio.sleep(1.0)
        data = {"rows": [[1,2,0],[2,1,1],[3,5,1]], "columns":["f1","f2","label"]}
        await self.log(job_id, f"DataAlchemist -> rows={len(data['rows'])}")

        # Iterative experiment loop
        for cycle in range(1, self.max_cycles+1):
            await self.log(job_id, f"Cycle {cycle}: ExperimentDesigner running tests...")
            await asyncio.sleep(1.0)
            results = {"metric": 0.62, "p_value": 0.08}
            await self.log(job_id, f"ExperimentDesigner -> {results}")

            await self.log(job_id, "Critic: evaluating results...")
            await asyncio.sleep(0.5)
            if results["p_value"] < 0.05:
                await self.log(job_id, "Critic: Passed. Finalizing.")
                break
            else:
                await self.log(job_id, "Critic: Failed threshold (p>=0.05). Requesting more iteration/data.")
                # Normally we'd trigger DataAlchemist to expand sources here
                await asyncio.sleep(0.5)

        await self.log(job_id, "Job finished: paper generation pending (stub).")
