# import io
# import keyboard
# from pydub import AudioSegment
# # import speech_recognition as sr
# import whisper
# import queue
# import tempfile
# import os
# import threading
# import torch
# import numpy as np
# import contextlib
#
# # Modified version of https://github.com/mallorbc/whisper_mic
# # Uses whisper https://github.com/openai/whisper
#
# # @click.command()
# # @click.option("--model", default="base", help="Model to use",
# #               type=click.Choice(["tiny", "base", "small", "medium", "large"]))
# # @click.option("--english", default=True, help="Whether to use English model", is_flag=True, type=bool)
# # @click.option("--verbose", default=False, help="Whether to print verbose output", is_flag=True, type=bool)
# # @click.option("--energy", default=300, help="Energy level for mic to detect", type=int)
# # @click.option("--dynamic_energy", default=False, is_flag=True, help="Flag to enable dynamic energy", type=bool)
# # @click.option("--pause", default=0.5, help="Pause time before entry ends", type=float)
# # @click.option("--save_file", default=False, help="Flag to save file", is_flag=True, type=bool)
#
#
# class SpeechRecWhisper:
#     def __init__(self):
#         self.result_queue = queue.Queue()
#         self.model = "base"
#         self.english = True
#         self.verbose = False
#         self.energy = 300
#         self.dynamic_energy = False
#         self.pause = 0.5
#         self.save_file = False
#         self.exit_request = False
#         self.thread_record = None
#         self.thread_transcribe = None
#
#         # there are no english models for large
#         if self.model != "large" and self.english and self.model in {"tiny", "base", "small", "medium"}:
#             self.model = f"{self.model}.en"
#         self.audio_model = whisper.load_model(self.model)
#
#     def run(self):
#         """
#         Starts speech to text
#         """
#         temp_dir = tempfile.mkd.temp() if self.save_file else None
#
#         audio_queue = queue.Queue()
#         self.exit_request = False
#
#         self.thread_record = threading.Thread(target=self.record_audio,
#                                               args=(audio_queue, temp_dir))
#         self.thread_record.start()
#         self.thread_transcribe = threading.Thread(target=self.transcribe_forever,
#                                                   args=(audio_queue, self.audio_model))
#         self.thread_transcribe.start()
#         # self.kill_threads()
#
#     def kill_threads(self):
#         """
#         Requests to kill recording and transcribing threads if alive
#         """
#         print("kill threads")
#         if self.thread_record is not None and self.thread_record.is_alive():
#             self.exit_request = True
#             self.thread_record.join()
#         if self.thread_transcribe is not None and self.thread_transcribe.is_alive():
#             self.exit_request = True
#             self.thread_transcribe.join()
#
#     def record_audio(self, audio_queue, temp_dir):
#         """
#         Uses SpeechRecognizer to capture voice
#         """
#         # load the speech recognizer and set the initial energy threshold and pause threshold
#         r = sr.Recognizer()
#         r.energy_threshold = self.energy
#         r.pause_threshold = self.pause
#         r.dynamic_energy_threshold = self.dynamic_energy
#         r.phrase_threshold = 0.4
#         r.non_speaking_duration = 0.1
#
#         with sr.Microphone(sample_rate=16000) as source:
#             r.adjust_for_ambient_noise(source, duration=0.5)
#             print("Say something!")
#             i = 0
#             while not self.exit_request:
#                 # get and save audio to wav file
#                 try:
#                     # print("audio")
#                     audio = r.listen(source, timeout=2, phrase_time_limit=None)
#                     print("audio2")
#                 except sr.WaitTimeoutError:
#                     continue
#
#                 if self.save_file:
#                     data = io.BytesIO(audio.get_wav_data())
#                     audio_clip = AudioSegment.from_file(data)
#                     filename = os.path.join(temp_dir, f"temp{i}.wav")
#                     audio_clip.export(filename, format="wav")
#                     audio_data = filename
#                 else:
#                     torch_audio = torch.from_numpy(
#                         np.frombuffer(audio.get_raw_data(), np.int16).flatten().astype(np.float32) / 32768.0)
#                     audio_data = torch_audio
#
#                 audio_queue.put_nowait(audio_data)
#                 i += 1
#
#     def transcribe_forever(self, audio_queue, audio_model):
#         """
#         Uses SpeechRecognizer to capture voice
#         """
#         while not self.exit_request:
#             try:
#                 # print("data1")
#                 audio_data = audio_queue.get(timeout=1)
#                 print("data2")
#             except queue.Empty:
#                 continue
#
#             print("data 3")
#             if self.english:
#                 result = audio_model.transcribe(audio_data, language='english')
#             else:
#                 result = audio_model.transcribe(audio_data)
#
#             print("data 4")
#             if not self.verbose:
#                 predicted_text = result["text"]
#                 self.result_queue.put_nowait(predicted_text)
#             else:
#                 self.result_queue.put_nowait(result)
#
#             if self.save_file:
#                 os.remove(audio_data)
#             print("data end\n")
#
#     def get_result_queue(self):
#         """
#         :return: Queue object containing transcribed text
#         """
#         return self.result_queue
#
#
# if __name__ == "__main__":
#     # Create speech recognizer class
#     srw = SpeechRecWhisper()
#     # Start recording and transcribing threads
#     srw.run()
#     while True:
#         # Get transcribed data
#         # By default, Queue.get() will block code until there is data to get from Queue
#         # Use optional get() parameter "timeout=1" seconds to time out the request, or use block=false
#         with contextlib.suppress(queue.Empty):
#             print(srw.get_result_queue().get())
#         if keyboard.is_pressed("a"):
#             print("You pressed 'a'.")
#             # Kill threads
#             srw.kill_threads()
