# higher-assembly-vm
#### Q: What is the HAVM (Higher assembly virtual machine)?

**A:** The HAVM is a VM written in python that runs a language called: **Higher assembly**,

#### Q: How it works? How programs are made in?

**A:** The HAVM works by taking a list of *instructions* and executes them one by one. Here's an example:
```has
[
  "PUTS", "i+", "Hello, World!", "",
  "END DATA"
]
```

#### Q: I want to run the VM but it dosen't works, how to fix?

**A:** Please check that you use the latest version of python (3.12.0) and you don't have modified something you shouldn't.

Else, please open up an issue.

# Basic overview of instructions

You should know that before all comes instructions in the HAVM,

Here's a basic overview to get you started:

    PUTS - arguments: [i+ / l+] <i+: [string: data]> <l+: [None]> -- Prints an user-provided value if argument i+ is used. If l+, prints from Register 10. --- Requires END DATA
    PUTSN - Same arguments as PUTS -- Prints an user-provided value WITHOUT \n if argument i+ is used. If l+, prints from Register 10. --- Requires END DATA
    PUSH - arguments: <to> <data> -- Push a value x to a register y. --- Requires END DATA
    PUSHA - arguments: <from> <to> -- Push a value x from register y to an argument position z.
    LOAD - arguments: <to> <value> -- Load a value x into a memory position y. --- Requires END DATA
    DELOAD - arguments: <location> -- Unloads a memory location x to register 10.
    END DATA -- Ends a data segment (REQUIRED FOR RESUMING EXECUTION)
