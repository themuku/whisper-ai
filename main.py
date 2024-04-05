from os import path, walk, makedirs, remove
from shutil import move
import whisper
import pydub
from fpdf import FPDF


def main():
    if not path.exists('audios'):
        makedirs('audios')  # Create a directory to store the audio files

    loop_through_files("audios")
    loop_through_files("mp3")
    loop_through_files("chunks")
    loop_through_files("transcripts")
    loop_through_files("delete")


def generate_mp3(file_path):
    print("Generating mp3 file for {}".format(file_path))
    audio = pydub.AudioSegment.from_file(file_path)

    if not path.exists('mp3'):
        makedirs('mp3')

    file_name = path.basename(file_path).split(".")[0]
    audio.export(f"mp3/{file_name}.mp3", format="mp3")

    print("Generated mp3 file for {}".format(file_path))


def chunk_audio(file_path):
    audio = pydub.AudioSegment.from_mp3(file_path)
    file_name = path.basename(file_path).split(".")[0]
    print("Length of original audio is ", len(audio) / 1000, " seconds")
    if not path.exists('chunks'):
        makedirs('chunks')
    chunk_length = 10 * 60 * 1000
    chunks = [audio[i:i + chunk_length] for i in range(0, len(audio), chunk_length)]
    for i, chunk in enumerate(chunks):
        chunk.export(f"chunks/{file_name}_chunk-{i}.mp3", format="mp3")
    print(f"Successfully split the audio file into {len(chunks)} chunks.")


def transcribe_audio(file_path):
    file_name = path.basename(file_path).split(".")[0].split("_")[0]
    print("Transcribing audio file {}".format(file_path))
    if not path.exists('transcripts'):
        makedirs('transcripts')
    model = whisper.load_model("tiny.en")
    result = model.transcribe(file_path)
    text = result["text"]

    chunks = []
    while text:
        if len(text) > 120:
            split_index = text.rfind(' ', 0, 120)
            if split_index == -1:
                split_index = 119
                chunks.append(text[:split_index+1] + "-")
            else:
                chunks.append(text[:split_index])
            text = text[split_index+1:]
        else:
            chunks.append(text)
            break

    text_with_newlines = '\n'.join(chunks)

    with open(f"transcripts/{file_name}.txt", "a", encoding='utf-8') as file:
        file.write(text_with_newlines)
        print("Transcribed audio file {} to {}.txt".format(file_path, file_name))


def txt_to_pdf(txt_file_path):
    pdf = FPDF()
    pdf.add_page()
    file_path = path.basename(txt_file_path)
    pdf.set_font("Arial", size=10)
    if not path.exists('pdf'):
        makedirs('pdf')
    with open(txt_file_path, "r", encoding='utf-8') as f:
        for line in f:
            # Replace non-'latin-1' characters with a placeholder
            line = line.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(200, 10, txt=line, ln=True)
    pdf_file_path = f"pdf/{file_path.replace(".txt", ".pdf")}"
    pdf.output(pdf_file_path)
    print(f"Converted {txt_file_path} to {pdf_file_path}")


def loop_through_files(folder_name):
    for folders, sub_folders, files in walk("."):
        if folder_name == "audios" and "audios" in folders:
            for file in files:
                if not file.endswith("mp3"):
                    file_path = path.join(folders, file)
                    generate_mp3(file_path)
                else:
                    move(file, "mp3")

        if folder_name == "mp3" and "mp3" in folders:
            for file in files:
                file_path = path.join(folders, file)
                chunk_audio(file_path)

        if folder_name == "chunks" and "chunks" in folders:
            for file in files:
                file_path = path.join(folders, file)
                transcribe_audio(file_path)

        if folder_name == "transcripts" and "transcripts" in folders:
            for file in files:
                file_path = path.join(folders, file)
                txt_to_pdf(file_path)

        if folder_name == "delete" and ("mp3" in folders or "chunks" in folders or "transcripts" in folders):
            for file in files:
                file_path = path.join(folders, file)
                remove(file_path)


if __name__ == '__main__':
    main()
