#!/usr/bin/python

import mock
import sys
import __builtin__

class ProductTest(mock.TestCase):
    
    def setUp(self):
        self.setupModules(["_isys", "block", 'os'])
        self.fs = mock.DiskIO()
        
        del sys.modules['pyanaconda.product']
        
        # os module global mock
        os = sys.modules['os']
        os.access = mock.Mock(return_value=False)
        os.environ = {}
        
        # fake /tmp/product/.buildstamp file
        self.ARCH = 'i386'
        self.STAMP = '123456.%s' % self.ARCH
        self.NAME = '__anaconda'
        self.VERSION = '14'
        self.FILENAME = '/tmp/product/.buildstamp'
        self.FILE = "%s\n%s\n%s\n" % (self.STAMP, self.NAME, self.VERSION)
        self.fs.open(self.FILENAME, 'w').write(self.FILE)
        
        # mock builtin open function
        self.open = __builtin__.open
        __builtin__.open = self.fs.open
        
    def tearDown(self):
        __builtin__.open = self.open
        self.tearDownModules()
    
    #
    # Default values
    #
    
    def default_product_stamp_test(self):
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productStamp, '')
    
    def default_product_name_test(self):
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productName, 'anaconda')
    
    def default_product_version_test(self):
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productVersion, 'bluesky')
        
    def default_product_arch_test(self):
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productArch, None)

    #
    # Info from environ variables
    #

    def product_version_from_environ_test(self):
        PRODUCTVERSION = '15'
        sys.modules['os'].environ['ANACONDA_PRODUCTVERSION'] = PRODUCTVERSION
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productVersion, PRODUCTVERSION)

    def product_name_from_environ_test(self):
        ENAME = 'anaconda__'
        sys.modules['os'].environ['ANACONDA_PRODUCTNAME'] = ENAME
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productName, ENAME)
    
    def product_arch_from_environ_test(self):
        PRODUCTARCH = 'x86_64'
        sys.modules['os'].environ['ANACONDA_PRODUCTARCH'] = PRODUCTARCH
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productArch, PRODUCTARCH)
    
    #
    # Info from file
    #
    
    def product_stamp_from_file_test(self):
        sys.modules['os'].access = mock.Mock(return_value=True)
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productStamp, self.STAMP)
    
    def product_name_from_file_test(self):
        sys.modules['os'].access = mock.Mock(return_value=True)
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productName, self.NAME)
    
    def product_version_from_file_test(self):
        sys.modules['os'].access = mock.Mock(return_value=True)
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productVersion, self.VERSION)
    
    def product_arch_from_file_test(self):
        sys.modules['os'].access = mock.Mock(return_value=True)
        import pyanaconda.product
        self.assertEqual(pyanaconda.product.productArch, self.ARCH)

