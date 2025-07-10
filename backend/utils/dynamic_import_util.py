import importlib



def import_class(module_name: str, class_name: str):
    """
    动态导入

    参数:
        module_name: 模块名 (e.g., "langchain_openai").
        class_name: 类名 (e.g., "ChatOpenAI").

    返回值:
        导入的类对象或是空
    """
    if not module_name or not class_name:
        return None
    try:
        module = importlib.import_module(module_name)
        imported_class = getattr(module, class_name)
        return imported_class
    except ImportError:
        print("动态导入时出现导入错误")
        return None
    except AttributeError as e:
        print("不存在的属性", e)
        return None
    except Exception as e:
        print("动态导入时，出现未知错误", e)
        return None
