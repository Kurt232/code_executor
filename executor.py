from kernel import interface
from kernel.ui_apis import CodeConfig, CodeStatus, regenerate_script, Verifier, ElementList
from kernel.api_doc import ApiDoc
class executor(object):
  '''
  '''
  def __init__(self, env: interface.AsyncEnv, code_config: CodeConfig, code_status: CodeStatus):
    self.env = env
    self.code_config = code_config
    self.code_status = code_status
    self.verifier = Verifier(self.env, self.code_config, self.code_status)
    
  def run(self):
    env = self.env
    verifier = self.verifier
    
    self.code_status.set_start_time()
    exec(self.code_config.compiled_code)
    self.code_status.set_end_time()

    return

if __name__ == '__main__':
  save_path = None 
  code = '''''' # todo::
  doc = ApiDoc() # todo::
  app_name = "" # ignore
  env = interface.AsyncMockEnv([], []) # todo::
  
  compiled_code,  line_mappings= regenerate_script(code, 'verifier')
  
  code_config = CodeConfig(app_name, doc, save_path, code, compiled_code, line_mappings)
  code_status = CodeStatus()
  
  runner = executor(env, code_config, code_status)
  
  done = False
  try:
    runner.run()
    done = True
  except Exception as e:
    print(e)
    pass
  
  print(f'{done=}')




