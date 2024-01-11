import logging
import os.path


from openai import OpenAI
from src.v1.services import files_services, mailgun_services


client = OpenAI()
# from transformers import pipeline
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

_logger = logging.getLogger(__name__)


def split_text(text, max_length):
    """
    Splits the text into chunks, each with a length less than or equal to max_length.
    """
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)
        if len(' '.join(current_chunk)) > max_length:
            chunks.append(' '.join(current_chunk[:-1]))
            current_chunk = [word]

    chunks.append(' '.join(current_chunk))  # Add the last chunk
    return chunks


def summary_extraction(chunk):
    messages = [
        {
            "role": "system",
            "content": "I have a very long meeting text, but it is too long to process in a signle transaction, can you summary the text for me and then I will sent you all of them in a single transaction to generate meeting notes",

        },
        {"role": "user", "content": chunk}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=messages,
    )
    return response.choices[0].message.content


def key_points_extraction(transcription):
    # summary_text = summarizer(transcription, max_length=10000, min_length=5000, do_sample=False)
    chunks = split_text(transcription, max_length=5000)
    summaries = []
    for item in chunks:
        summaries.append(summary_extraction(item))
    summary_text = ". ".join(summaries)
    messages = [
        {
            "role": "system",
            "content": "Can you generate meeting notes for me? I want have a Meeting Notes title which is the abstract of the meeting, and i want to have overview and have details to do list and want to have confirmation or actions needed.",

        },
        {"role": "user", "content": summary_text}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0,
        messages=messages,
    )
    return response.choices[0].message.content


def save_as_docx(minutes, filename):
    doc = Document()
    for key, value in minutes.items():
        # Replace underscores with spaces and capitalize each word for the heading
        heading = " ".join(word.capitalize() for word in key.split("_"))
        doc.add_heading(heading, level=1)
        doc.add_paragraph(value)
        # Add a line break between sections
        doc.add_paragraph()
    doc.save(filename)


def meeting_captions(transcription, file_id, filename):
    key_points = key_points_extraction(transcription)
    result = {"Key points": key_points}
    file_name, file_ext = os.path.splitext(filename)
    save_as_docx(result, f"uploads/{file_id}/{file_name}.docx")
    return key_points


def generate_key_points(file_id) -> bool:
    """
    Generate key points and save it into database
    Args:
        transcription: the text generated from file_id
        file_id: current file uuid

    Returns:
        Status
    """
    try:
        file_info, status = files_services.get_file(file_id)
        key_points = meeting_captions(file_info.full_text_result, file_id, file_info.filename)
        file_info = files_services.save_meeting_note(file_id, key_points)
        mailgun_services.send_mailgun_email(
            to=file_info['created_by']['email'],
            subject=f"Key points note for {file_info['filename']}",
            text=key_points
        )
        return True
    except Exception as ex:
        _logger.exception(ex)
        return False
