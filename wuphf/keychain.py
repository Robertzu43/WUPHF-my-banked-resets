import ctypes

SERVICE=b'WUPHF My Resets'


def _security():
    lib=ctypes.CDLL('/System/Library/Frameworks/Security.framework/Security')
    lib.SecKeychainFindGenericPassword.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.POINTER(ctypes.c_uint32),ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(ctypes.c_void_p)]
    lib.SecKeychainAddGenericPassword.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_char_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p)]
    lib.SecKeychainItemModifyAttributesAndData.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p]
    lib.SecKeychainItemFreeContent.argtypes=[ctypes.c_void_p,ctypes.c_void_p]
    return lib


def _find(lib, key):
    key=key.encode();length=ctypes.c_uint32();data=ctypes.c_void_p();item=ctypes.c_void_p()
    status=lib.SecKeychainFindGenericPassword(None,len(SERVICE),SERVICE,len(key),key,ctypes.byref(length),ctypes.byref(data),ctypes.byref(item))
    return status, length, data, item


def get_secret(key):
    if not key: raise ValueError('Key required')
    lib=_security();status,length,data,item=_find(lib,key)
    if status==-25300: return None
    if status: raise OSError('Keychain could not be accessed')
    try: return ctypes.string_at(data,length.value).decode()
    finally:
        lib.SecKeychainItemFreeContent(None,data)
        ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation').CFRelease(ctypes.c_void_p(item.value))


def set_secret(key,value):
    if not key: raise ValueError('Key required')
    if not isinstance(value,str) or not value: raise ValueError('Secret required')
    lib=_security();status,length,data,item=_find(lib,key)
    value=value.encode();buf=ctypes.create_string_buffer(value)
    if status==-25300:
        key=key.encode();status=lib.SecKeychainAddGenericPassword(None,len(SERVICE),SERVICE,len(key),key,len(value),buf,None)
    elif status==0:
        lib.SecKeychainItemFreeContent(None,data)
        try: status=lib.SecKeychainItemModifyAttributesAndData(item,None,len(value),buf)
        finally: ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation').CFRelease(ctypes.c_void_p(item.value))
    if status: raise OSError('Keychain could not be updated')


def delete_secret(key):
    if not key: raise ValueError('Key required')
    lib=_security();status,length,data,item=_find(lib,key)
    if status==-25300:return
    if status:raise OSError('Keychain could not be accessed')
    lib.SecKeychainItemFreeContent(None,data)
    try:
        lib.SecKeychainItemDelete.argtypes=[ctypes.c_void_p]
        if lib.SecKeychainItemDelete(item):raise OSError('Keychain item could not be deleted')
    finally:
        ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation').CFRelease(ctypes.c_void_p(item.value))
