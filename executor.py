from kernel import interface
from kernel.ui_apis import CodeConfig, CodeStatus, regenerate_script, Verifier, ElementList

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




