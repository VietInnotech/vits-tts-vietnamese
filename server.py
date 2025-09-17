import tornado.ioloop
import tornado.web
import tornado.gen
from validate import validate_query_params
from tts import text_to_speech, text_to_speech_streaming
import hashlib
import os
import argparse

# Define a JSON schema for your query parameters
query_param_schema = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "speed": {"type": "string", "maxLength": 9}
    },
    "required": ["text", "speed"]
}

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('web/index.html')

class MyHandler(tornado.web.RequestHandler):
    @validate_query_params(query_param_schema)
    def get(self):
        # Parameters are already validated here
        text:str = self.get_argument('text')
        speed:str = self.get_argument('speed')
        current_url:str = '{}://{}'.format(self.request.protocol,self.request.host)
        result,file_name = handle_tts_request(text,speed)
        result["audio_url"] =  current_url+"/audio/"+file_name
        self.write(result)
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class StreamingTTSHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    @validate_query_params(query_param_schema)
    def get(self):
        # Parameters are already validated here
        text:str = self.get_argument('text')
        speed:str = self.get_argument('speed')
        
        # Set appropriate headers for audio streaming
        self.set_header('Content-Type', 'audio/wav')
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Pragma', 'no-cache')
        
        try:
            # Generate audio data using the streaming function
            audio_buffer = text_to_speech_streaming(text, speed, "pretrained_vi.onnx")
            
            # Stream the audio data in chunks
            chunk_size = 8192  # 8KB chunks
            while True:
                chunk = audio_buffer.read(chunk_size)
                if not chunk:
                    break
                self.write(chunk)
                yield self.flush()  # Ensure data is sent immediately
            
            # Finish the response
            self.finish()
            
        except Exception as e:
            self.set_status(500)
            self.write({"error": str(e)})
            self.finish()
    
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

def make_app(enable_ui=True):
    handlers = [
        (r"/tts", MyHandler),
        (r"/tts/stream", StreamingTTSHandler),
        (r'/audio/(.*)', tornado.web.StaticFileHandler, {'path': os.getcwd()+"/audio/"}),
        (r'/assets/(.*)', tornado.web.StaticFileHandler, {'path': os.getcwd()+"/assets/"}),
    ]
    
    if enable_ui:
        handlers.append((r'/', HomeHandler))
    
    return tornado.web.Application(handlers)

def handle_tts_request(text,speed):
    text_hash:str = hashlib.sha1((text+speed).encode('utf-8')).hexdigest()
    file_name = text_hash+ ".wav"
    file_path = os.getcwd()+"/audio/"+file_name
    if os.path.isfile(file_path):
        return ({
            "hash":text_hash,
            "text":text,
            "speed":speed,
            },file_name)
    else:
        # create new file 
        model_name = "pretrained_vi.onnx"
        audio_path = text_to_speech(text,speed,model_name,text_hash)
        return ({
            "hash":text_hash,
            "text":text,
            "speed":speed,
            },file_name)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TTS Server')
    parser.add_argument('--no-ui', action='store_true', help='Disable the web interface')
    args = parser.parse_args()
    
    app = make_app(enable_ui=not args.no_ui)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
