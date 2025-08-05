from asyncio import to_thread
from io import BytesIO

from fastapi import FastAPI, Form, UploadFile
from pdf2image import convert_from_bytes

# from phoenix.otel import register
from pydantic import BaseModel
from pypdf import PdfReader
from smolagents import ActionStep, CodeAgent, LiteLLMModel, tool

from .prompts import SYSTEM_PROMPT
from .settings import settings

# tracer_provider = register(
#     endpoint="http://localhost:6006/v1/traces",
#     project_name="smolagents-app",
#     auto_instrument=True,
# )

app = FastAPI()


# ------------------------------------------------------------------
# 1. PDFState class to encapsulate PDF data and navigation state
# ------------------------------------------------------------------
class PDFState:
    """Encapsulates PDF document state and navigation."""

    def __init__(self, pdf_bytes: bytes):
        self.pdf_bytes = pdf_bytes
        self.current_page = 0  # 0-based index

        # Get total page count
        try:
            all_pages = convert_from_bytes(pdf_bytes, dpi=1)  # Lower DPI for faster counting
            self.total_pages = len(all_pages)
        except Exception:
            self.total_pages = 1

    def get_page_image(self, page_index: int = None):
        """Return PIL.Image for the given page (or current page if not specified)."""
        if page_index is None:
            page_index = self.current_page

        if page_index < 0 or page_index >= self.total_pages or self.pdf_bytes is None:
            return None

        return convert_from_bytes(
            self.pdf_bytes, dpi=150, first_page=page_index + 1, last_page=page_index + 1
        )[0]

    def next_page(self) -> str:
        """Move to the next page."""
        self.current_page = min(self.current_page + 1, self.total_pages - 1)
        reader = PdfReader(BytesIO(self.pdf_bytes))
        page_text = reader.pages[self.current_page].extract_text()
        return (
            f"Switched to page {self.current_page + 1}. Page text: {page_text}"
            if page_text
            else f"Switched to page {self.current_page + 1}."
        )

    def previous_page(self) -> str:
        """Move to the previous page."""
        self.current_page = max(self.current_page - 1, 0)
        reader = PdfReader(BytesIO(self.pdf_bytes))
        page_text = reader.pages[self.current_page].extract_text()
        return (
            f"Switched to page {self.current_page + 1}. Page text: {page_text}"
            if page_text
            else f"Switched to page {self.current_page + 1}."
        )

    def go_to_page(self, page_number: int) -> str:
        """Move to the specified page (1-based)."""
        # Convert to 0-based index
        page_index = page_number - 1
        self.current_page = min(max(page_index, 0), self.total_pages - 1)
        reader = PdfReader(BytesIO(self.pdf_bytes))
        page_text = reader.pages[self.current_page].extract_text()
        return (
            f"Switched to page {self.current_page + 1}. Page text: {page_text}"
            if page_text
            else f"Switched to page {self.current_page + 1}."
        )


# ------------------------------------------------------------------
# 2. Agent runner with closures for tools
# ------------------------------------------------------------------
async def run_agent(pdf_bytes: bytes, question: str):
    """Run the agent with the given PDF and question."""
    # Create PDF state
    pdf_state = PDFState(pdf_bytes)

    # Create tools as closures that capture the pdf_state
    @tool
    def next_page() -> str:
        """Move to the next page and return a note including the new page number."""
        return pdf_state.next_page()

    @tool
    def previous_page() -> str:
        """Move to the previous page and return a note."""
        return pdf_state.previous_page()

    @tool
    def go_to_page(page_number: int) -> str:
        """Move to the specified page and return a note.
        Args:
            page_number: The page number to move to (1-based).
        """
        return pdf_state.go_to_page(page_number)

    # Create callback that captures pdf_state
    def current_page_callback(memory_step: ActionStep, agent: CodeAgent) -> None:
        current_step = memory_step.step_number
        for (
            previous_memory_step
        ) in agent.memory.steps:  # Remove previous screenshots from logs for lean processing
            if (
                isinstance(previous_memory_step, ActionStep)
                and previous_memory_step.step_number <= current_step - 2
            ):
                previous_memory_step.observations_images = None
        memory_step.observations_images = [
            pdf_state.get_page_image()
        ]  # Create a copy to ensure it persists
        return

    # Create and configure agent
    agent = CodeAgent(
        tools=[next_page, previous_page, go_to_page],
        model=LiteLLMModel(
            model_id=f"hosted_vllm/{settings.model_id}",
            api_base=settings.api_base,
            api_key=settings.api_key,
        ),
        additional_authorized_imports=["*"],
        step_callbacks=[current_page_callback],
        verbosity_level=0,
    )

    agent.prompt_templates["system_prompt"] = SYSTEM_PROMPT

    answer = await to_thread(agent.run, question, images=[pdf_state.get_page_image()])

    return Response(answer=answer, page=pdf_state.current_page + 1)


# ------------------------------------------------------------------
# 3. FastAPI endpoint
# ------------------------------------------------------------------
class Response(BaseModel):
    answer: str | list[str]
    page: int


@app.post("/ask_pdf", response_model=Response)
async def ask_pdf(file: UploadFile, question: str = Form(...)):
    pdf_bytes = await file.read()

    return await run_agent(pdf_bytes, question)


# ------------------------------------------------------------------
# 4. Main function for testing
# ------------------------------------------------------------------
async def main():
    with open("tests/test.pdf", "rb") as f:
        pdf_bytes = f.read()

    question = "Was ist die Servicenummer?"
    result = await run_agent(pdf_bytes, question)
    print(f"Question: {question}")
    print(f"Answer: {result}")


# ------------------------------------------------------------------
# 5. FastAPI server runner
# ------------------------------------------------------------------
def run_server():
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
