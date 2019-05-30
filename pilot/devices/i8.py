def getDevice(model, module, compiler):
  return I8Device(model, module, compiler)

class I8Device():
  compiler = None
  model = None
  module = None
  size = 1

  def __init__(self, model, module, compiler):
    self.size = 1
    self.compiler = compiler
    self.module = module
    self.model = model
  
  def include(self):
    return ['i8.h']

  def source(self):
    return """// source for device {}
    
void {0}_read()
{
    *target = 0;
    $i8.Inputs:{input| *target |= GPIO_ReadInputDataBit($input.GPIO$, $input.Pin$) << $i0$; };separator="\n"$
\}
    
    """.format(self.module['device']['name'])