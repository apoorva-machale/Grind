"""
Part C: YAML Prompt Versioning & PromptManager (Ollama Mistral)
CloudCart Version-Controlled Prompt Management

This module demonstrates:
1. Loading YAML 4-layer prompt architecture (v1.0.0, v1.1.0)
2. Symlink-based version management for zero-downtime updates
3. PromptManager class for loading, compiling, and invoking
4. Version upgrade workflow with Ollama Mistral
5. Production-grade deployment patterns
"""

import os
import yaml
import json
from typing import Dict, List, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.llms import Ollama


# ============================================================================
# OLLAMA MISTRAL SETUP
# ============================================================================

def get_ollama_llm():
    """
    Initialize Ollama Mistral LLM.
    
    Prerequisites:
    1. Install Ollama: https://ollama.ai
    2. Pull Mistral: ollama pull mistral
    3. Run: ollama serve (in background)
    
    Configuration optimized for support agent:
    - Low temperature (0.3) for consistent responses
    - Response length limited to 200 tokens
    """
    llm = Ollama(
        model="mistral",
        base_url="http://localhost:11434",
        temperature=0.3,
        top_p=0.9,
        top_k=40,
        num_predict=200
    )
    return llm


# ============================================================================
# C.2: DIRECTORY STRUCTURE & SYMLINK MANAGEMENT
# ============================================================================

class PromptVersionManager:
    """
    Manages prompt versioning with symlinks for zero-downtime updates.
    
    Directory structure:
    prompts/
    ├── cloudcart/
    │   ├── v1.0.0.yaml     # Tagged release
    │   ├── v1.1.0.yaml     # New release
    │   └── current.yaml    # Symlink → v1.1.0.yaml (active version)
    
    Why symlinking matters for zero-downtime:
    1. Atomic switch: Change symlink → instantly use new prompt
    2. Rollback: Revert symlink to previous version in seconds
    3. Testing: Test new version before updating symlink
    4. No code changes: Existing code reads 'current.yaml' automatically
    5. Audit trail: Keep all versions for compliance and debugging
    """
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.path.join(os.path.dirname(__file__), "prompts")
        
        self.base_path = Path(base_path)
        self.cloudcart_path = self.base_path / "cloudcart"
    
    def get_cloudcart_path(self) -> Path:
        """Get the CloudCart prompts directory"""
        return self.cloudcart_path
    
    def verify_files_exist(self) -> Tuple[bool, List[str]]:
        """Verify that YAML files exist. Returns (success, error_messages)"""
        errors = []
        
        if not self.cloudcart_path.exists():
            errors.append(f"Directory not found: {self.cloudcart_path}")
            return False, errors
        
        v1_0_0_path = self.cloudcart_path / "v1.0.0.yaml"
        v1_1_0_path = self.cloudcart_path / "v1.1.0.yaml"
        
        if not v1_0_0_path.exists():
            errors.append(f"v1.0.0.yaml not found at {v1_0_0_path}")
        
        if not v1_1_0_path.exists():
            errors.append(f"v1.1.0.yaml not found at {v1_1_0_path}")
        
        return len(errors) == 0, errors
    
    def create_current_symlink(self, target_version: str) -> Tuple[bool, str]:
        """
        Create or update symlink to make a version "current".
        Enables zero-downtime updates by switching symlink target.
        
        Args: target_version: Version string like "1.0.0" or "1.1.0"
        Returns: (success, message)
        """
        current_link = self.cloudcart_path / "current.yaml"
        target_file = f"v{target_version}.yaml"
        target_path = self.cloudcart_path / target_file
        
        # Verify target file exists
        if not target_path.exists():
            return False, f"Target file not found: {target_file}"
        
        try:
            # Remove existing symlink if present
            if current_link.exists() or current_link.is_symlink():
                current_link.unlink()
            
            # Create new symlink
            current_link.symlink_to(target_file)
            
            message = f"✅ Created symlink: current.yaml → {target_file}"
            return True, message
        
        except Exception as e:
            return False, f"Error creating symlink: {str(e)}"
    
    def get_current_version_path(self) -> Tuple[bool, Path, str]:
        """Get path to current prompt version (through symlink). Returns (success, path, message)"""
        current_link = self.cloudcart_path / "current.yaml"
        
        if not current_link.exists():
            return False, None, "current.yaml symlink not found"
        
        try:
            if current_link.is_symlink():
                target = current_link.resolve()
                message = f"current.yaml → {target.name}"
                return True, current_link, message
            else:
                return True, current_link, "current.yaml (direct file)"
        except Exception as e:
            return False, None, f"Error resolving symlink: {str(e)}"
    
    def get_version_info(self) -> Dict[str, Any]:
        """Get information about current and available versions"""
        current_link = self.cloudcart_path / "current.yaml"
        version_files = sorted(self.cloudcart_path.glob("v*.yaml"))
        
        info = {
            "base_path": str(self.cloudcart_path),
            "available_versions": [f.stem for f in version_files],
            "current_version": None,
            "current_target": None,
            "symlink_valid": False
        }
        
        if current_link.exists():
            if current_link.is_symlink():
                try:
                    target = current_link.resolve()
                    info["current_target"] = target.name
                    info["current_version"] = target.stem
                    info["symlink_valid"] = True
                except:
                    info["symlink_valid"] = False
            else:
                info["current_version"] = "current.yaml (direct file)"
        
        return info


# ============================================================================
# C.3: PROMPTMANAGER CLASS
# ============================================================================

@dataclass
class PromptSchema:
    """Type-safe schema definition for prompt inputs"""
    variables: List[Dict[str, Any]] = field(default_factory=list)
    
    def validate(self, variables_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate input variables against schema"""
        errors = []
        
        for var_spec in self.variables:
            var_name = var_spec["name"]
            
            if var_spec.get("required") and var_name not in variables_dict:
                errors.append(f"Required variable missing: {var_name}")
                continue
            
            if var_name in variables_dict:
                value = variables_dict[var_name]
                expected_type = var_spec.get("type", "string")
                
                if not isinstance(value, str if expected_type == "string" else object):
                    errors.append(f"Variable {var_name} has wrong type")
                
                if "max_length" in var_spec and len(str(value)) > var_spec["max_length"]:
                    errors.append(f"Variable {var_name} exceeds max_length {var_spec['max_length']}")
        
        return len(errors) == 0, errors


class PromptManager:
    """
    Manages loading, compiling, and invoking versioned prompts from YAML files.
    
    Workflow:
    1. load(path) → Parse YAML and validate structure
    2. compile() → Build ChatPromptTemplate from layers
    3. invoke(variables) → Validate inputs and call Ollama Mistral
    """
    
    def __init__(self, prompt_path: str = None):
        """Initialize with optional prompt path"""
        self.prompt_data = None
        self.template = None
        self.llm = get_ollama_llm()
        self.schema = None
        
        if prompt_path:
            self.load(prompt_path)
    
    def load(self, path: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Load and parse prompt YAML file.
        
        Validates:
        - File exists and is readable
        - YAML is valid
        - All 4 layers are present
        
        Returns: (success, data, message)
        """
        path_obj = Path(path)
        
        if not path_obj.exists():
            return False, None, f"Prompt file not found: {path}"
        
        try:
            with open(path_obj, 'r') as f:
                self.prompt_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return False, None, f"Invalid YAML: {e}"
        except Exception as e:
            return False, None, f"Error reading file: {e}"
        
        # Validate 4-layer structure
        required_layers = ["metadata", "system_prompt", "few_shot_examples", "input_schema"]
        missing_layers = [layer for layer in required_layers if layer not in self.prompt_data]
        if missing_layers:
            return False, None, f"Missing prompt layers: {missing_layers}"
        
        # Extract schema
        self.schema = PromptSchema(
            variables=self.prompt_data.get("input_schema", {}).get("variables", [])
        )
        
        message = (f"✅ Loaded prompt: {path_obj.name}\n"
                  f"   Version: {self.prompt_data['metadata'].get('version')}\n"
                  f"   Scenario: {self.prompt_data['metadata'].get('scenario')}")
        
        return True, self.prompt_data, message
    
    def compile(self) -> Tuple[bool, ChatPromptTemplate, str]:
        """
        Compile YAML layers into ChatPromptTemplate.
        
        Combines:
        - System prompt + constraints + output format
        - Few-shot examples as context
        - Input schema for validation
        
        Returns: (success, template, message)
        """
        if not self.prompt_data:
            return False, None, "No prompt loaded. Call load() first."
        
        try:
            # Build system message from Layer 2
            system_parts = []
            sp = self.prompt_data["system_prompt"]
            
            system_parts.append(f"Role: {sp.get('role', '')}")
            system_parts.append(f"\nDescription:\n{sp.get('role_description', '')}")
            
            if sp.get("constraints"):
                system_parts.append("\nConstraints:")
                for constraint in sp["constraints"]:
                    system_parts.append(f"- {constraint}")
            
            if sp.get("prohibited_behaviors"):
                system_parts.append("\nProhibited Behaviors:")
                for behavior in sp["prohibited_behaviors"]:
                    system_parts.append(f"✗ {behavior}")
            
            if sp.get("output_format"):
                system_parts.append(f"\nResponse Format: {sp['output_format'].get('type', 'json')}")
                fields = sp['output_format'].get('fields', {})
                system_parts.append("Required fields: " + ", ".join(fields.keys()))
            
            system_message_content = "\n".join(system_parts)
            
            # Build few-shot examples from Layer 3
            few_shot_text = "\nExamples:\n"
            for i, example in enumerate(self.prompt_data.get("few_shot_examples", []), 1):
                few_shot_text += f"\n{i}. Input: {example.get('input', '')}\n"
                few_shot_text += f"   Output: {json.dumps(example.get('output', {}), indent=2)}\n"
            
            system_message_content += few_shot_text
            
            # Create template
            self.template = ChatPromptTemplate.from_messages([
                SystemMessage(content=system_message_content),
                HumanMessage(content="{user_input}")
            ])
            
            return True, self.template, "✅ Compiled prompt template"
        
        except Exception as e:
            return False, None, f"Error compiling template: {str(e)}"
    
    def invoke(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate inputs and invoke prompt with Ollama Mistral.
        
        Returns: LLM response with metadata
        """
        if not self.template:
            return {
                "success": False,
                "errors": ["No template compiled. Call compile() first."],
                "response": None
            }
        
        # Validate against schema
        is_valid, errors = self.schema.validate(variables)
        if not is_valid:
            return {
                "success": False,
                "errors": errors,
                "response": None
            }
        
        try:
            # Invoke chain with Ollama Mistral
            print("\n[Invoking Ollama Mistral LLM...]")
            chain = self.template | self.llm
            result = chain.invoke(variables)
            
            # Try to parse as JSON
            try:
                response_json = json.loads(result)
            except json.JSONDecodeError:
                response_json = {"raw_response": result}
            
            return {
                "success": True,
                "errors": [],
                "response": response_json
            }
        except Exception as e:
            print(f"❌ Error invoking Ollama: {str(e)}")
            print("\nMake sure Ollama is running:")
            print("  1. Install: https://ollama.ai")
            print("  2. Pull: ollama pull mistral")
            print("  3. Run: ollama serve")
            
            return {
                "success": False,
                "errors": [f"LLM invocation error: {str(e)}"],
                "response": None
            }
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get prompt metadata"""
        if not self.prompt_data:
            return {}
        return self.prompt_data.get("metadata", {})


# ============================================================================
# C.4: VERSION UPGRADE DEMONSTRATION
# ============================================================================

def demonstrate_version_upgrade():
    """Demonstrates upgrading from v1.0.0 to v1.1.0 with actual YAML files"""
    print("\n" + "=" * 80)
    print("PART C.4: VERSION UPGRADE DEMONSTRATION (WITH OLLAMA MISTRAL)")
    print("=" * 80)
    
    version_manager = PromptVersionManager()
    
    # Verify files exist
    print("\n### Phase 0: Verify YAML Files ###")
    exists, errors = version_manager.verify_files_exist()
    if not exists:
        print("❌ YAML files not found:")
        for error in errors:
            print(f"   {error}")
        return
    
    print("✅ Found YAML files:")
    print(f"   Location: {version_manager.cloudcart_path}")
    
    # Phase 1: Setup current symlink to v1.0.0
    print("\n### Phase 1: Current Production (v1.0.0) ###")
    success, message = version_manager.create_current_symlink("1.0.0")
    print(message)
    
    info = version_manager.get_version_info()
    print(f"Available versions: {info['available_versions']}")
    print(f"Current version: {info['current_version']}")
    
    # Phase 2: Load and use v1.0.0
    print("\n### Phase 2: Using Current Version (v1.0.0) ###")
    manager_v1 = PromptManager()
    success, current_path, msg = version_manager.get_current_version_path()
    if success:
        success, data, msg = manager_v1.load(str(current_path))
        print(msg)
        
        success, template, msg = manager_v1.compile()
        if success:
            print(f"{msg}")
    
    # Phase 3: Prepare v1.1.0
    print("\n### Phase 3: Prepare New Version (v1.1.0) ###")
    v1_1_0_path = version_manager.cloudcart_path / "v1.1.0.yaml"
    print(f"✅ v1.1.0 already saved at: {v1_1_0_path}")
    print("   (Ready for testing - not yet live)")
    
    # Phase 4: Test v1.1.0
    print("\n### Phase 4: Test New Version (Pre-Switch) ###")
    manager_v1_1 = PromptManager()
    success, data, msg = manager_v1_1.load(str(v1_1_0_path))
    if success:
        v1_1_metadata = manager_v1_1.get_metadata()
        print(f"Version: {v1_1_metadata.get('version')}")
        print(f"Improvements:")
        for imp in v1_1_metadata.get('improvements', []):
            print(f"  ✨ {imp}")
    
    # Phase 5: Switch to v1.1.0
    print("\n### Phase 5: Go Live with v1.1.0 (Zero-Downtime Switch) ###")
    success, message = version_manager.create_current_symlink("1.1.0")
    print(message)
    print("🚀 v1.1.0 is now live!")
    print("   All code reading 'current.yaml' automatically uses v1.1.0")
    
    # Phase 6: Verify switch
    print("\n### Phase 6: Verify Switch ###")
    info = version_manager.get_version_info()
    print(f"Current version: {info['current_version']}")
    print(f"Current target: {info['current_target']}")
    
    # Phase 7: Rollback capability
    print("\n### Phase 7: Rollback Capability ###")
    print("If v1.1.0 has issues, rollback is instant:")
    print("  ln -sf v1.0.0.yaml prompts/cloudcart/current.yaml")
    print("All code automatically reverts to v1.0.0 (no deployment needed!)")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("CLOUDCART SECURE PROMPT MANAGEMENT - PART C")
    print("YAML Prompt Versioning with Ollama Mistral")
    print("=" * 80)
    
    print("\ This version uses actual YAML files with Ollama Mistral LLM:")
    print("   - prompts/cloudcart/v1.0.0.yaml")
    print("   - prompts/cloudcart/v1.1.0.yaml")
    print("   - prompts/cloudcart/current.yaml (symlink)")
    
    # Check directory
    vm = PromptVersionManager()
    print(f"\nPrompts directory: {vm.cloudcart_path}")
    
    exists, errors = vm.verify_files_exist()
    if not exists:
        print("\n❌ YAML files not found!")
        print("Error details:")
        for error in errors:
            print(f"   - {error}")
        return
    
    # Run demonstrations
    demonstrate_version_upgrade()
    
    print("\n" + "=" * 80)
#     print("SUMMARY")
#     print("=" * 80)
#     print("""
# ✅ PRODUCTION-GRADE YAML VERSIONING WITH OLLAMA MISTRAL:

# YAML 4-Layer Architecture:
# - Layer 1 (Metadata): Version, author, scenario, created_at
# - Layer 2 (System Prompt): Role, constraints, prohibitions
# - Layer 3 (Few-Shot Examples): Training examples
# - Layer 4 (Input Schema): Variable definitions

# Symlink Strategy (zero-downtime):
# - prompts/cloudcart/current.yaml → v1.0.0.yaml
# - Switch: ln -sf v1.1.0.yaml current.yaml
# - All servers instantly use new version (<1 second)
# - Instant rollback: ln -sf v1.0.0.yaml current.yaml

# PromptManager with Ollama Mistral:
# - load(): Parse YAML from actual files
# - compile(): Build ChatPromptTemplate
# - invoke(): Call Ollama Mistral LLM
# - Uses local Mistral model (no API keys)

# OLLAMA MISTRAL BENEFITS:
# - Free, open-source model
# - Local inference (privacy-preserving)
# - No API calls or external dependencies
# - Works offline
# - Lower latency for small queries
# - Full control over the model

# PRODUCTION WORKFLOW:
# 1. Edit v1.1.0.yaml (improved system prompt)
# 2. Deploy to servers (no switch yet)
# 3. Test with real traffic
# 4. Switch symlink: ln -sf v1.1.0.yaml current.yaml
# 5. Monitor with Ollama Mistral
# 6. Rollback if needed: ln -sf v1.0.0.yaml current.yaml

# BUSINESS VALUE:
# - Update prompts without code deployment
# - Zero downtime (symlink switch is atomic)
# - Instant rollback capability
# - Full version history for compliance
# - Local LLM = no vendor lock-in
# """)


if __name__ == "__main__":
    main()
