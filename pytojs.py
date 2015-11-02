import ast

testscript = """
def testfun(a, b, *args):
	return a + b + c
testfun(1,2,c=3, d=Error)
"""

root = ast.parse(testscript)

def print_fields(node):
	for f in node._fields:
		print(f, getattr(node, f))

def print_attributes(node):
	print("\n\n", node)
	for f in node._attributes:
		print(f, getattr(node, f))

class Visor(ast.NodeVisitor):
	indent_count = 0
	blocks = [{'vars': [], 'id': 'root'}]
	def indent_up(self):
		self.indent_count += 1
	def indent_down(self):
		self.indent_count -= 1
	def indent(self, s, indent=None):
		if indent:
			return ("\t" * indent) + s
		return ("\t" * self.indent_count) + s

	def add_var_to_cur_block(self, var_id):
		if var_id not in self.blocks[-1]['vars']:
			self.blocks[-1]["vars"].append(var_id)

	def new_block(self):
		self.indent_up()
		self.blocks.append({
			'vars': []
		})

	def end_block(self):
		self.indent_down()
		self.blocks.remove(self.blocks[-1])

	def block_vars(self):
		if len(self.blocks[-1]['vars']):
			return "var " + ", ".join(self.blocks[-1]["vars"]) + ';\n'
		else:
			return "\n"

	def visit_Num(self, node):
		return str(node.n)

	def visit_Name(self, node):
		return str(node.id)

	def visit_And(self, node):
		return " && "
	def visit_Or(self, node):
		return " || "
	def visit_Not(self, node):
		return "!"

	def visit_BoolOp(self, node):
		print_fields(node)
		op = self.visit(node.op)
		ret_string = op.join([self.visit(comp) for comp in node.values])
		return ret_string

	def visit_List(self, node):
		ret_string = '['
		for el in node.elts:
			ret_string += self.visit(el)
			if el != node.elts[-1]:
				ret_string += ', '
		return ret_string + ']'

	def visit_Dict(self, node):
		ret_string = "{\n"
		self.indent_up()
		for idx, key in enumerate(node.keys):
			ret_string += self.indent(self.visit(key) + ": " + self.visit(node.values[idx])) + '\n'
		self.indent_down()
		return ret_string + '}'

	def visit_Subscript(self, node):
		if type(node.slice) == ast.Slice:
			return self.visit_Slice(node.slice, node)
		return self.visit(node.value) + '[' + self.visit(node.slice) + ']'

	def visit_Slice(self, node, context):
		ret_string = self.visit(context.value) + '.slice(' + self.visit(node.lower) + ', ' + self.visit(node.upper)
		if node.step:
			ret_string += ", " + self.visit(node.step)
		return ret_string + ')'

	def visit_Index(self, node):
		return self.visit(node.value)

	def visit_Str(self, node):
		return '"' + node.s + '"'


	def visit_NameConstant(self, node):
		if node.value == None:
			return "null"
		elif node.value == False:
			return "false"
		elif node.value == True:
			return "true"
		else:
			return str(node.value)

	def visit_Add(self, node):
		return " + "
	def visit_Sub(self, node):
		return " - "
	def visit_Mult(self, node):
		return " * "
	def visit_Div(self, node):
		return " / "
	def visit_Mod(self, node):
		return " % "
	def visit_BitAnd(self, node):
		return " & "
	def visit_BitOr(self, node):
		return " | "
	def visit_BitXor(self, node):
		return " ^ "
	def visit_RShift(self, node):
		return " >> "
	def visit_LShift(self, node):
		return " << "
	def visit_Pow(self, node, context):
		return "Math.pow(" + self.visit(context.left) + ", " + self.visit(context.right) + ")"
	def visit_FloorDiv(self, node, context):
		return 'Math.floor(' + self.visit(context.left) + ' / ' + self.visit(context.right) + ')'

	def visit_Invert(self, node):
		return '~'

	def visit_Gt(self, node):
		return " > "
	def visit_Lt(self, node):
		return " < "
	def visit_GtE(self, node):
		return " >= "
	def visit_LtE(self, node):
		return " <= "
	def visit_Eq(self, node):
		return " == "
	def visit_NotEq(self, node):
		return " != "


	def visit_In(self, node, context):
		return "$$In$$(" + self.visit(context.left) + ', ' + self.visit(context.comparators[0]) + ')'
	def visit_NotIn(self, node, context):
		return "!" + self.visit_In(node, context)

	def visit_UAdd(self, node):
		return "+"
	def visit_USub(self, node):
		return "-"

	def visit_UnaryOp(self, node):
		return self.visit(node.op) + '(' + self.visit(node.operand) + ')'

	def visit_AugAssign(self, node):
		return self.visit(node.target) + self.visit(node.op).rstrip() + '= ' + self.visit(node.value) 

	def visit_Break(self, node):
		return self.indent('break')
	def visit_Continue(self, node):
		return self.indent('continue')
	def visit_Pass(self, node):
		return self.indent('// Empty function')

	def visit_For(self, node):
		ret_string = "for(var " + self.visit(node.target) + " of " + self.visit(node.iter) + ")"
		ret_string += self.handle_body(node.body)
		return ret_string

	def visit_While(self, node):
		ret_string = "while (" + self.visit(node.test) + ')'
		ret_string += self.handle_body(node.body)
		return ret_string

	def visit_Compare(self, node):

		if type(node.ops[0]) == ast.NotIn:
			return self.visit_NotIn(node.ops[0], node)

		ret_string = self.visit(node.left)
		for op in node.ops:

			ret_string += self.visit(op)
		for comp in node.comparators:
			ret_string += self.visit(comp)
		return ret_string

	def visit_If(self, node):
		ret_string = "if (" + self.visit(node.test) + ")"
		ret_string += self.handle_body(node.body)
		if node.orelse:
			ret_string += " else " + self.handle_body(node.orelse)
		return ret_string

	def visit_BinOp(self, node):
		if type(node.op) == ast.Pow:
			return self.visit_Pow(node.op, node)
		elif type(node.op) == ast.FloorDiv:
			return self.visit_FloorDiv(node.op, node)

		return '(' + self.visit(node.left) + self.visit(node.op) + self.visit(node.right) + ')'

	def visit_arguments(self, node):
		# args []
		# vararg None
		# kwonlyargs []
		# kw_defaults []
		# kwarg None
		# defaults []
		print_fields(node)
		print_attributes(node)
		print(node.args, node.vararg, node.kwonlyargs, node.kw_defaults, node.kwarg, node.defaults)
		for arg in node.args:
			print_fields(arg)
		ret_arr = []
		for idx, arg in enumerate(node.args):
			if idx >= (len(node.args) - len(node.defaults)):
				ret_arr.append(self.visit(arg) + "=" + self.visit(node.defaults[idx - len(node.args)]))
			else:
				ret_arr.append(self.visit(arg))
		if node.vararg:
			ret_arr.append('...' + self.visit(node.vararg))

		return "(" + ", ".join(ret_arr) + ")"

	def visit_arg(self, node):
		return node.arg

	def visit_Return(self, node):
		return "return " + self.visit(node.value)

	def handle_body(self, body, inject=None, brackets=True):
		self.new_block()
		ret_string = ''
		if brackets: ret_string += ' { \n'
		if inject: ret_string += self.indent(inject)
		ret_string += self.indent('$$pytojs__blockvars$$\n')

		for child_node in body:
			ret_string += self.indent(self.visit(child_node) + ";\n")

		block_vars = self.block_vars()

		ret_string = ret_string.replace('$$pytojs__blockvars$$\n', block_vars)

		self.end_block()

		if brackets: ret_string += self.indent('}')
		return ret_string

	def visit_FunctionDef(self, node):

		ret_string =  "function " + node.name + self.visit(node.args)
		ret_string += self.handle_body(node.body)
		return ret_string

	def visit_ClassDef(self, node):
		self.new_block()
		
		extends = ""
		extends = ",".join([self.visit(base_node) for base_node in node.bases])
		print("\n\n EXTNEDS", extends)

		ret_string = "class " + node.name + " {\n"
		for child_node in node.body:
			ret_string += self.indent(self.visit(child_node) + ";\n")

		self.end_block()
		
		return self.indent(ret_string + '}')

	def visit_Tuple(self, node):
		print_fields(node)
		return '[' + ', '.join([self.visit(el) for el in node.elts]) + ']'

	def visit_Assign(self, node):
		print_fields(node)
		res_string = ''
		for t in node.targets:
			self.add_var_to_cur_block(self.visit(t))
			res_string += self.visit(t)
			if t != node.targets[-1]:
				res_string += ' = '

		res_string += " = "
		res_string += self.visit(node.value)
		return res_string

	def visit_Delete(self, node):
		print_fields(node)
		return self.indent("delete " + ', '.join([self.visit(el) for el in node.targets]) + ';')

	def visit_Attribute(self, node):
		return self.visit(node.value) + "." + node.attr

	def visit_Expr(self, node):
		return self.visit(node.value)

	def visit_keyword(self, node):
		return node.arg + '=' + self.visit(node.value)

	def parse_args(self, args, kw, kwargs, starargs):
		args_list = []
		args_list += [self.visit(arg) for arg in args]
		for idx, k in enumerate(kw):
			args_list += [self.visit(k)]

		return "(" + ", ".join(args_list) + ")"

	def visit_Call(self, node):
		arg_str = self.parse_args(node.args, node.keywords, node.kwargs, node.starargs)
		return self.visit(node.func) + arg_str

	def visit_comprehension(self, node):
		print("\n\nCompre")
		print_fields(node)
		ret_string = 'for (' + self.visit(node.target) + ' of ' + self.visit(node.iter) + ') '
		for if_ in node.ifs:
			ret_string += 'if (' + self.visit(if_) + ') '
		return ret_string

	def visit_DictComp(self, node):
		raise NotImplementedError("Dict comprehensions are not available in ECMA 6")

	def visit_ListComp(self, node):
		print_fields(node)
		ret_string = ''
		for generator in node.generators:
			return '[' + self.visit(generator) + '\n' + self.indent(self.visit(node.elt), indent=1) + ']'

	def visit_Raise(self, node):
		return 'throw new ' + self.visit(node.exc)

	def visit_ExceptHandler(self, node):
		print("\n\nExcept Handler")
		print_fields(node)
		ret_string = ''
		print(node.type, node.type == None)
		ret_string += self.indent('if ($$py_error$$')
		if node.type != None:
			ret_string += ' instanceof ' + self.visit(node.type) + ')'
		else: ret_string += ')'
		inject = None
		if node.name:
			inject = 'var ' + node.name + ' = $$py_error$$;'
		ret_string += self.handle_body(node.body, inject=inject) + '\n'

		return ret_string


	def visit_Try(self, node):
		print_fields(node)
		ret_string = 'try' + self.handle_body(node.body)
		if len(node.handlers):
			ret_string += ' catch ($$py_error$$) {\n'
			self.indent_up()
			for handler in node.handlers:
				ret_string += self.visit(handler)
			for orelse in node.orelse:
				ret_string += ' else ' + self.handle_body(node.orelse)
			ret_string += '}'
			self.indent_down()

		if node.finalbody:
			ret_string += self.indent(' finally')
			ret_string += self.handle_body(node.finalbody)
		return ret_string




	def generic_visit(self, node):
		print(node)
		return "Not Implemented"
		print(node)



vis = Visor()
vis.visit(root)

for node in ast.iter_child_nodes(root):
	r = vis.visit(node)

	print(vis.block_vars() + r)

# print(ast.dump(root))