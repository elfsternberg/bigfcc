#!/usr/local/bin/python

from StringIO import StringIO
import string
import sys
import time

class WriteSentry:
    '''
    Purpose: WriteSentry encapsulates the way an output file is written
    to.  It also provides a convenient way to open, write to, and close
    a file, merely by declaring a WriteSentry object in a given Python
    scope.  When the WriteSentry object goes out of scope, the __del__
    method is called, and the file is flushed and closed.
    '''

    VERBOSE = 1;
    OVERWRITE = 2;
    
    def __init__( self, fileName, mode, reallyCreate = 1 ):
        mode = mode or self.VERBOSE
        self.outputFile = None
        if reallyCreate:
            bCreateTheFile = ( mode & self.OVERWRITE ) != 0
            if not bCreateTheFile:
                try:
                    fd = open( fileName, "r" );
                    self.outputFile = open( "/dev/null", "w" )
                    if ( mode & self.VERBOSE ):
                        print "Did NOT create " + fileName + " because it already exists."
                        fd.close
                except:
                    bCreateTheFile = 1;
                            
                if bCreateTheFile:
                    try:
                        self.outputFile = open( fileName, "w" )
                        if ( mode & self.VERBOSE ):
                            print "Created " + fileName + "\n"
                    except IOError, e:
                        print "Could not create file " + str( e )
                        raise

    def __del__( self ):        
        if self.outputFile != None:
            self.outputFile.close()

    def getStream( self ):
        return self.outputFile



class DigestedCommands:

    usage = \
        "*******************************************************************************\n" + \
        "Fast Class Creator Version 2.35b, Created by John F. Hubbard, 20 April 2001\n" + \
        "Ported to Python 13 May 2001 by Elf M. Sternberg\n\n" + \
        "Usage: fcc -class <list_of_class_names> (see example below)\n" + \
        "           -author <authors_name>  \n" + \
        "          [-namespace <namespace_name> | -ns <namespace_name>]\n" + \
        "          [-overwrite | -ow]\n" + \
        "          [-verbose | -v]\n" + \
        "          [-no_unit_test | -no_ut]\n" + \
        "          [-no_makefile | -no_mf]\n" + \
        "          [-project <project_name>]\n" + \
        "          [-sccs_keywords | -sccs]\n" + \
        "          [-continuus_keywords | -ct]\n" + \
        "          [-open_source_notice | -os]\n" + \
        "          [-copyright <copyright> | -c <copyright>]\n" + \
        "          [-base_filename <base_filename> | -file <base_filename>]\n" + \
        "          [-no_copy_ctor]\n" + \
        "          [-no_assignment_operator | -no_op =]\n" + \
        "          [-no_ctor]\n" + \
        "          [-no_dtor]\n" + \
        "          [-public_copy_ctor]\n" + \
        "          [-public_assignment_operator | -pub_op =]\n" + \
        "          [-no_dump_diagnostics | -no_dd]\n" + \
        "          [-no_check_valid | -no_cv]\n" + \
        "          [-no_icc]\n" + \
        "          [-settings_file <filename>]\n\n" + \
        "Abbreviations: ctor = constructor, dtor = destructor\n\n" + \
        "A simple example:\n\n" + \
        "    fcc -verbose -class Airplane -namespace airport -author \"John F. Hubbard\"\n\n" + \
        "This example generates several classes in the same set of FruitFiles.xxx files:\n\n" + \
        "    fcc -file FruitFiles -class Apple Orange Pear " + \
                                        "-ns fruits -author \"John F. Hubbard\"\n\n" + \
        "*******************************************************************************\n\n"

    def __init__( self, arglist = sys.argv[1:] ):
        j = 0
        self.arglist = arglist
        self.argkeys = {}
        for i in arglist:
            self.argkeys[i] = j
            j = j + 1

        if not ( self.argkeys.has_key( "-class" ) and self.argkeys.has_key( "-author" ) ):
            raise self.usage

        self.classList = self.getArgument( "-class" )
        self.author = self.getArgument( "-author" )

        # Added to support multiple classes per file, and control of copy/assignment:
        self.sccsKeywords       = ( self.argkeys.has_key( "-sccs_keywords" ) or
                                    self.argkeys.has_key( "-sccs" ) )
        self.continuousKeywords = ( self.argkeys.has_key( "-continuus_keywords" ) or
                                    self.argkeys.has_key( "-ct" ) )
        self.openSourceNotice   = ( self.argkeys.has_key( "-open_source_notice" ) or
                                    self.argkeys.has_key( "-os" ) )

        if self.argkeys.has_key( "-copyright" ):
            self.copyright = self.getArgument( "-copyright" )
        
        elif self.argkeys.has_key( "-c" ):
            self.copyright = self.getArgument( "-c" )
        else:
            self.copyright = \
                         " * Put Your Copyright Notice here\n"

        self.createUnitTestFile =  not ( self.argkeys.has_key( "-no_unit_test" ) or
                                    self.argkeys.has_key( "-no_ut" ) )
        self.createMakefile     =  not ( self.argkeys.has_key( "-no_makefile" ) or
                                    self.argkeys.has_key( "-no_mf" ) )
        self.ctor               = not self.argkeys.has_key( "-no_ctor" )
        self.dtor               = not self.argkeys.has_key( "-no_dtor" )
        self.iccFile            = not self.argkeys.has_key( "-no_icc" )
        self.checkValid         = not ( self.argkeys.has_key( "-no_check_valid" ) or
                                   self.argkeys.has_key( "-no_cv" ) )
        self.dumpDiagnostics    = not ( self.argkeys.has_key( "-no_dump_diagnostics" ) or
                                   self.argkeys.has_key( "-no_dd" ) )
        self.useNamespace       = self.argkeys.has_key( "-namespace" ) or self.argkeys.has_key( "-ns" )
        self.dtor               = not self.argkeys.has_key( "-no_dtor" )
        self.copyCtor           = self.ctor and not self.argkeys.has_key( "-no_copy_ctor" )
        self.assignmentOperator = not ( self.argkeys.has_key( "-no_assignment_operator" ) or
                                   self.argkeys.has_key( "-no_op =" ) )
        self.publicCopyCtor     = self.argkeys.has_key( "-public_copy_ctor" ) and self.copyCtor
        self.publicAssignmentOperator =   self.assignmentOperator and \
                                   ( self.argkeys.has_key( "-public_assignment_operator" ) or
                                     self.argkeys.has_key( "-pub_op =" ) )

        self.writeSentryMode = 0

        if ( self.argkeys.has_key( "-verbose" ) or self.argkeys.has_key( "-v" ) ):
            self.writeSentryMode = self.writeSentryMode | WriteSentry.VERBOSE
        
        if ( self.argkeys.has_key( "-overwrite" ) or self.argkeys.has_key( "-ow" ) ):
            self.writeSentryMode = self.writeSentryMode | WriteSentry.OVERWRITE

        if self.argkeys.has_key( "-project" ):
            self.projectName = self.getArgument( "-project" );
        
        if self.argkeys.has_key( "-namespace" ):
            self.namespace = self.getArgument( "-namespace" );
        elif self.argkeys.has_key( "-ns" ):
            self.namespace = self.getArgument( "-ns" );

        self.classNames = self.getArglist( "-class" )

        if self.argkeys.has_key( "-base_filename" ):
            self.baseFilename = self.getArgument( "-base_filename" );
        elif self.argkeys.has_key( "-file" ):
            self.baseFilename = self.getArgument( "-file" )
        else:
            self.baseFilename = self.classNames[0]

        self.headerFile = self.baseFilename + ".h"
        self.implFile = self.baseFilename + ".cpp"
        self.inlineFile = self.baseFilename + ".icc"
        self.makefile = "makefile"
        self.unitTestFile = "ut" + self.baseFilename + ".cpp"


    def getArgument( self, arg ):
        loc = self.argkeys[ arg ] + 1
        rep = self.arglist[ loc ]
        if string.find( rep, "-" ) == 0:
            raise self.usage
        return rep

    def getArglist( self, arg ):
        loc = self.argkeys[ arg ] + 1
        rep = []
        while( ( loc < len( self.arglist ) ) and
               ( string.find( self.arglist[ loc ], "-" ) == -1 ) ):
            rep.append( self.arglist[ loc ] )
            loc = loc + 1
        if ( len( rep ) == 0 ):
            raise self.usage
        return rep



class CodeGenerator:

    def __init__( self, commands ):
        self.commands = commands

    def genCommentHeader( self ):
        pass

    def genPreface( self ):
        pass

    def genCodeBody( self, className ):
        pass

    def genEpilogue( self ):
        pass

    def generateDefaultCommentHeader( self, fileName, io_str ):
        print >> self.getStream(), \
        "/*****************************************************************************\n" + \
        " *\n" + \
        " *  " + fileName + "\n" + \
        " *  Created by " + self.commands.author + ", on " + dateStamp() + "\n" + \
        " *\n" + \
        " *  " + self.commands.copyright + "\n" + \
        " *\n",
        
        if self.commands.openSourceNotice:
            print >> self.getStream(), \
            " *  Permission is granted to use this code without restriction,\n" + \
            " *  as long as this copyright notice appears in all source files.\n" + \
            " *\n",

        print >> self.getStream(), io_str.getvalue(),

        if self.commands.continuousKeywords:
            print >> self.getStream(), \
            " *  %version: 1 %\n" + \
            " *  %date_modified: " + dateStamp() + " %\n" + \
            " *  %created_by: " + self.commands.author + " %\n",

        if self.commands.sccsKeywords:
            print >> self.getStream(), \
            " *  Version: %I%\n" + \
            " *  Date modified: %G%\n" + \
            " *\n"
        print >> self.getStream(), \
        " *****************************************************************************\n" + \
        " */\n\n",



    def generateDefaultPreface( self, fileName, io_str ):
        print >> self.getStream(), \
        "#include <string>\n" + \
        "#include <iostream>\n" + \
        "#include \"" + self.commands.headerFile + "\"\n",

        print >> self.getStream(), io_str.getvalue()



    def createUniqueName( self ):
        if self.commands.useNamespace:
            return string.upper(self.commands.namespace) + "_" + \
                   string.upper(self.commands.baseFilename) + "_H"
        else:
            return string.upper(self.commands.baseFilename) + "_H"



def dateStamp():
    return time.asctime( time.localtime( time.time() ) )



class HeaderFileGen( CodeGenerator ):

    def __init__( self, commands ):
        self.commands = commands
        self.writer = WriteSentry( self.commands.headerFile,
                                   self.commands.writeSentryMode )

    def getStream( self ):
        return self.writer.getStream()

    
    def genCommentHeader( self ):
        io_str = StringIO()
        print >> io_str, " *\n" + \
            " *  File Contents: Interface and documentation of the " + \
            self.commands.baseFilename + " component.\n" + \
            " *\n",
        self.generateDefaultCommentHeader( self.commands.headerFile,  io_str )



    def genPreface( self ):                         
        print >> self.getStream(), \
        "#ifndef " + self.createUniqueName() + "\n" + \
        "#define " + self.createUniqueName() + "\n\n",

        if self.commands.useNamespace:
            print >> self.getStream(), \
            "namespace " + self.commands.namespace + "\n" + \
            "{\n" + \
            " \n",



    def genCodeBody(self, className ): 
        print >> self.getStream(), "/** Purpose: TODO: Describe the purpose of the class.\n" + \
            " *  (Everything that you write here will show up in the\n" + \
            " *  doc++ generated documentation.)\n" + \
            " */\n" + \
            "class " + className + "\n" + \
            "{\n" + \
            "public:\n",

        if self.commands.ctor:
            print >> self.getStream(), "    /// Constructor.\n" + \
            "    " + className + "();\n\n",
            
        if self.commands.dtor:
            print >> self.getStream(), "    /// Destructor.\n" + \
                  "    virtual ~" + className + "();\n",

        if self.commands.checkValid:
            print >> self.getStream(), " \n" + \
            "    /// CheckValid() is designed to check the class invariants.\n" + \
            "    inline CheckValid() const;\n",
            
        if self.commands.dumpDiagnostics:
            print >> self.getStream(), " \n" + \
            "    /// DumpDiagnostics() dumps the object's state to standard output.\n" + \
            "    DumpDiagnostics() const;\n" + \
            " \n",

        if self.commands.publicCopyCtor:
            print >> self.getStream(), "public:\n" + \
            "    // TODO: Provide an implementation for the copy constructor:\n" + \
            "    " + className + "(const " + className + "&);\n\n",

        elif self.commands.copyCtor:
            print >> self.getStream(), "private:\n" + \
            "    // Copying of this class is prohibited:\n" + \
            "    " + className + "(const " + className + "&);\n\n",

        if self.commands.publicAssignmentOperator:
            print >> self.getStream(), "public:\n" + \
            "    // TODO: Provide an implementation for the assignment operator:\n" + \
            "    " + className + "& operator=(const " + className + "&);\n\n",

        elif self.commands.assignmentOperator:
            print >> self.getStream(), "private:\n" + \
            "    // Assignment to this class is prohibited:\n" + \
            "    " + className + "& operator=(const " + className + "&);\n\n",

        print >> self.getStream(), "};\n",



    def genEpilogue( self ):
        if self.commands.iccFile:
            print >> self.getStream(), " \n" + \
                "#include \"" + self.commands.inlineFile + "\"\n",

        if self.commands.useNamespace:
            print >> self.getStream(), "} // end of the " + self.commands.namespace + " namespace\n\n",

        print >> self.getStream(), "#endif /* " + self.createUniqueName() + " */\n\n",




class ImplFileGen( CodeGenerator ):

    def __init__( self, commands ):
        self.commands = commands
        self.writer = WriteSentry( self.commands.implFile,
                                   self.commands.writeSentryMode)

    def getStream( self ):
        return self.writer.getStream()

    def genCommentHeader( self ):
        io_str = StringIO()
        print >> io_str, " *\n" + \
            " *  File Contents: Implementation of the " + self.commands.baseFilename + " component.\n" + \
            " *  Please see " + self.commands.headerFile + " for full documentation of this system.\n" + \
            " *\n",
        self.generateDefaultCommentHeader( self.commands.implFile, io_str )

    def genPreface( self ):
        io_str = StringIO()
        self.generateDefaultPreface( self.commands.implFile, io_str  )
        if ( self.commands.useNamespace ):
            print >> self.getStream(), "namespace " + self.commands.namespace + "\n" + \
            "{\n" + \
            " \n"


    def genCodeBody( self, className ):
        if self.commands.ctor :
                print >> self.getStream(), \
                    className + "::" + className + "()\n" + \
                    "{\n" + \
                    "}\n"

        if self.commands.dtor:
            print >> self.getStream(),        className + "::~" + \
                     className + "()\n" + \
            "{\n" + \
            "}\n"

        if self.commands.dumpDiagnostics:
            print >> self.getStream(), "void\n" + \
                className + "::DumpDiagnostics() const\n" + \
                "{\n",

            print >> self.getStream(), '    std::cout << std::endl << std::endl << \n' + \
                "    \"" + className + \
                " Diagnostics dump \"<< std::endl << std::endl;\n",

            print >> self.getStream(), "}\n"

    def genEpilogue( self ):
        if self.commands.useNamespace:
                print >> self.getStream(), \
                    " \n" + \
                    "} // end of the " + self.commands.namespace + " namespace"



class InlineFileGen( CodeGenerator ):

    def __init__( self, commands ):
        self.commands = commands
        self.writer = WriteSentry( commands.inlineFile, commands.writeSentryMode )
        
    def getStream( self ):
        return self.writer.getStream()

    def genCommentHeader( self ):
        io_str = StringIO()
        print >> io_str,  " *\n" + \
            " *  File Contents: Inline definitions for the " + self.commands.baseFilename + \
            " component.\n" + \
            " *  Please see " + self.commands.headerFile + " for full documentation of this class.\n" + \
            " *\n",
        self.generateDefaultCommentHeader( self.commands.inlineFile, io_str );

    def genCodeBody( self, className ):
        if self.commands.checkValid:
            print >> self.getStream(), "inline void\n" + \
                className + "::CheckValid() const\n" + \
                "{\n" + \
                "    // TODO: Fill in with class invariant assertions for " + \
                className + ".\n" + \
                "}\n"



class MakefileGen( CodeGenerator ):

    def __init__( self, commands ):
        self.commands = commands
        self.writer = WriteSentry( self.commands.makefile,
                                   self.commands.writeSentryMode,
                                   self.commands.createMakefile )
        
    def getStream( self ):
        return self.writer.getStream()
    

    def genCommentHeader( self ):
        print >> self.getStream(), \
        "#########################################################################\n" + \
        "#  " + self.commands.makefile + "\n" + \
        "#  Created by " + self.commands.author + " on " + dateStamp()  + "\n" + \
        "#\n" + \
        "#  File Contents: makefile for the " + self.commands.baseFilename + " component.\n" + \
        "#\n" + \
        "#########################################################################\n\n"

    def genPreface( self ):
        print >> self.getStream(), "NAME=" + self.commands.baseFilename

        print >> self.getStream(), "INCLUDES=\n" + \
            "LIBS=\n" + \
            "CC=gcc\n" + \
            "CXX=g++\n" + \
            "LD=g++\n" + \
            "LD_FLAGS=\n\n" + \
            "all: ut${NAME} html\n\n" + \
            "html: ${NAME}.h \n" + \
            "\tdoc++ -d html *.h\n" + \
            "\ttouch html\n\n" + \
            "CXX_FLAGS=-DLINUX -g -c -fhonor-std \\\n" + \
            "          -fno-builtin -D_REENTRANT -Wall -Wno-unknown-pragmas -Wno-unused\n\n" + \
            "ut${NAME} : ut${NAME}.o ${NAME}.o\n" + \
            "\t${LINK} ${LINK_FLAGS} -o ut${NAME} ut${NAME}.o ${NAME}.o ${LIBS}\n\n" + \
            "${NAME}.o : ${NAME}.cpp ${NAME}.h",

        if self.commands.iccFile:
            print >> self.getStream(), " ${NAME}.icc",
            
        print >> self.getStream(), "\n" + \
            "\t${CXX} ${CXX_FLAGS} ${INCLUDES} -c -o ${NAME}.o ${NAME}.cpp\n\n" + \
            "ut${NAME}.o : ut${NAME}.cpp ${NAME}.h",

        if self.commands.iccFile:
            print >> self.getStream(), " ${NAME}.icc",

        print >> self.getStream(), "\n" + \
            "\t${CXX} ${CXX_FLAGS} ${INCLUDES} -c -o ut${NAME}.o ut${NAME}.cpp\n\n" + \
            "clean:\n" + \
            "\trm *.o ut${NAME} html/" "*\n" + \
            "\trmdir html"



class UnitTestFileGen(CodeGenerator):

    def __init__( self, commands ):
        self.commands = commands
        self.writer = WriteSentry( self.commands.unitTestFile,
                                   self.commands.writeSentryMode,
                                   self.commands.createUnitTestFile )
        
    def genCommentHeader( self ):
        io_str = StringIO()
        print >> io_str, " *\n" + \
            " *  File Contents: Unit test for the the " + self.commands.baseFilename +" component.\n" + \
            " *  Please see " + self.commands.headerFile +" for full documentation of this class.\n" + \
            " *\n"
        self.generateDefaultCommentHeader( self.commands.unitTestFile, io_str )

    def genPreface( self ):
        io_str = StringIO()
        self.generateDefaultPreface( self.commands.unitTestFile, io_str )
        print >> self.getStream(),        "int main(int argc, char* argv[])\n" + \
            "{\n"


    def genCodeBody( self, className ):
        if self.commands.useNamespace:
            print >> self.getStream(), "    " + self.commands.namespace +"::"

        print >>self.getStream(), className +" obj" + className +";\n"

        if self.commands.dumpDiagnostics:
            print >> self.getStream(), "    obj" + className +".DumpDiagnostics();\n"

        print >> self.getStream(), "\n"

    def genEpilogue( self ):
        print >> self.getStream(), "    return 0;\n" + \
            "}\n"

    def getStream( self ):
        return self.writer.getStream()




class ClassCreator:

    def __init__( self, commands ):
        self.commands = commands

    def generateCode( self ):
        self.generateFile( HeaderFileGen )
        self.generateFile( ImplFileGen )

        if self.commands.iccFile:
            self.generateFile( InlineFileGen )

        if self.commands.createMakefile:
            self.generateFile( MakefileGen )

        if self.commands.createUnitTestFile:
            self.generateFile( UnitTestFileGen )

    def generateFile( self, inclass ):
        generator = inclass( self.commands )

        generator.genCommentHeader();   # The comment header with author, description, etc.
        generator.genPreface();         # #ifdef directives, for example.

        for i in self.commands.classNames:
            generator.genCodeBody( i ); # generate each class.

        generator.genEpilogue();



commands = DigestedCommands( )
creator = ClassCreator( commands )
creator.generateCode()



