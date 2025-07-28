import base64

from openai import OpenAI
from smolagents import Tool

SYSTEM_PROMPT = """You are an expert document information extractor that specializes in analyzing document images and answering questions with precision. Your task is to:

1. Carefully examine the provided document image/page
2. Extract relevant information that directly answers the question
3. Be precise and factual - only provide information that is clearly visible in the document
4. If the specific information requested is not present or not clearly readable in the current page, respond with "No answer in page"
5. When information is found, provide direct quotes or specific details from the document
6. For numerical data, dates, names, or specific terms, be exact in your extraction
7. If asked about document structure or layout, describe what you observe accurately

Focus on being a reliable information extraction tool rather than making inferences beyond what is explicitly shown in the document."""


# Function to encode the image
def encode_image(image_path):
    """Helper function to encode local image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class VisualQATool(Tool):
    name = "visual_qa_tool"
    description = "A tool that can answer questions about PIL images."
    inputs = {
        "image": {
            "description": "The PIL Image object on which to answer the question",
            "type": "image",
        },
        "question": {"description": "the question to answer", "type": "string"},
    }
    output_type = "string"

    def __init__(self, model_id: str, api_base: str, api_key: str):
        super().__init__()
        self.model_id = model_id
        self.client = OpenAI(api_key=api_key, base_url=api_base)

    def forward(self, image, question: str) -> str:
        """Process PIL Image and question using OpenAI chat completions"""
        try:
            # Convert PIL Image to base64
            import io

            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                            },
                        ],
                    },
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in visual QA: {e}")
            return f"Error processing image: {str(e)}"


def main():
    """Main function to test the VisualQATool"""
    from settings import settings

    # Create the VisualQA tool instance
    visual_qa_tool = VisualQATool(
        model_id=settings.model_id, api_base=settings.api_base, api_key=settings.api_key
    )

    # Load test.png from current directory and ask specific question
    image_path = "test.png"
    question = "Was ist der Monatsbeitrag ab 01.11.18?"

    try:
        print(f"Processing image: {image_path}")
        print(f"Question: {question}")
        print("=" * 50)

        # Encode the image to base64
        base64_image = encode_image(image_path)

        # Run the visual QA
        result = visual_qa_tool(base64_image=base64_image, question=question)
        print("Answer:")
        print(result)

    except FileNotFoundError:
        print(f"Error: Image file '{image_path}' not found.")
    except Exception as e:
        print(f"Error processing request: {e}")


if __name__ == "__main__":
    main()
