"""
React Analyzer - Deep analysis of React/TypeScript components

Analyzes:
- Component structure and hierarchy
- Props and state usage
- Hooks and custom hooks
- Dependencies and imports
- Styling patterns (Tailwind, CSS-in-JS, etc.)
- API calls and data fetching
- Lovable-specific patterns
"""

import os
import re
from typing import Dict, List, Optional, Set
from pathlib import Path
import json


class ReactAnalyzer:
    """
    Analyze React/TypeScript components for patterns and structure
    """

    def __init__(self, project_path: str):
        """
        Initialize React analyzer

        Args:
            project_path: Path to React project root
        """
        self.project_path = Path(project_path)
        self.src_path = self.project_path / "src"

        # Analysis results
        self.components: Dict[str, Dict] = {}
        self.hooks: Set[str] = set()
        self.dependencies: Dict[str, Set[str]] = {}

    def analyze_project(self) -> Dict:
        """
        Analyze entire React project

        Returns:
            Complete analysis results
        """
        print(f"[ReactAnalyzer] Analyzing project: {self.project_path}")

        if not self.src_path.exists():
            raise Exception(f"Source directory not found: {self.src_path}")

        # Find all component files
        component_files = self._find_component_files()
        print(f"[ReactAnalyzer] Found {len(component_files)} component files")

        # Analyze each component
        for file_path in component_files:
            self._analyze_component_file(file_path)

        # Analyze project structure
        structure = self._analyze_project_structure()

        # Identify patterns
        patterns = self._identify_patterns()

        return {
            "components": self.components,
            "hooks": list(self.hooks),
            "dependencies": {k: list(v) for k, v in self.dependencies.items()},
            "structure": structure,
            "patterns": patterns,
            "stats": self._calculate_stats()
        }

    def _find_component_files(self) -> List[Path]:
        """Find all React component files"""
        component_files = []

        for ext in ['.tsx', '.jsx', '.ts', '.js']:
            component_files.extend(self.src_path.rglob(f'*{ext}'))

        return component_files

    def _analyze_component_file(self, file_path: Path):
        """
        Analyze a single component file

        Args:
            file_path: Path to component file
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        component_name = file_path.stem

        # Extract component information
        component_info = {
            "path": str(file_path.relative_to(self.project_path)),
            "name": component_name,
            "type": self._detect_component_type(content),
            "props": self._extract_props(content),
            "state": self._extract_state_usage(content),
            "hooks": self._extract_hooks(content),
            "imports": self._extract_imports(content),
            "exports": self._extract_exports(content),
            "styling": self._detect_styling_approach(content),
            "api_calls": self._detect_api_calls(content),
            "patterns": self._detect_component_patterns(content)
        }

        self.components[component_name] = component_info

        # Track hooks
        self.hooks.update(component_info["hooks"])

        # Track dependencies
        self.dependencies[component_name] = set(component_info["imports"])

    def _detect_component_type(self, content: str) -> str:
        """Detect component type (functional, class, etc.)"""
        if re.search(r'class\s+\w+\s+extends\s+(?:React\.)?Component', content):
            return "class"
        elif re.search(r'(?:const|let|var|export)\s+\w+\s*=\s*\(.*?\)\s*=>', content):
            return "functional_arrow"
        elif re.search(r'function\s+\w+\s*\(', content):
            return "functional"
        else:
            return "unknown"

    def _extract_props(self, content: str) -> List[str]:
        """Extract props interface/type"""
        props = []

        # Match TypeScript interface
        interface_match = re.search(r'interface\s+\w+Props\s*\{([^}]+)\}', content)
        if interface_match:
            props_content = interface_match.group(1)
            # Extract prop names
            prop_matches = re.findall(r'(\w+)(?:\?)?:', props_content)
            props.extend(prop_matches)

        # Match TypeScript type
        type_match = re.search(r'type\s+\w+Props\s*=\s*\{([^}]+)\}', content)
        if type_match:
            props_content = type_match.group(1)
            prop_matches = re.findall(r'(\w+)(?:\?)?:', props_content)
            props.extend(prop_matches)

        return list(set(props))

    def _extract_state_usage(self, content: str) -> List[str]:
        """Extract state variables (useState)"""
        state_vars = []

        # Match useState calls
        use_state_matches = re.findall(r'const\s+\[(\w+),\s*set\w+\]\s*=\s*useState', content)
        state_vars.extend(use_state_matches)

        return state_vars

    def _extract_hooks(self, content: str) -> List[str]:
        """Extract React hooks used"""
        hooks = set()

        # Built-in hooks
        builtin_hooks = ['useState', 'useEffect', 'useContext', 'useReducer',
                        'useCallback', 'useMemo', 'useRef', 'useLayoutEffect']

        for hook in builtin_hooks:
            if hook in content:
                hooks.add(hook)

        # Custom hooks (start with 'use')
        custom_hook_matches = re.findall(r'(?:const|let|var)\s+\w+\s*=\s*(use\w+)\(', content)
        hooks.update(custom_hook_matches)

        return list(hooks)

    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements"""
        imports = []

        # Match ES6 imports
        import_matches = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content)
        imports.extend(import_matches)

        # Match dynamic imports
        dynamic_matches = re.findall(r'import\([\'"]([^\'"]+)[\'"]\)', content)
        imports.extend(dynamic_matches)

        return list(set(imports))

    def _extract_exports(self, content: str) -> List[str]:
        """Extract exported items"""
        exports = []

        # Match default export
        if 'export default' in content:
            default_match = re.search(r'export\s+default\s+(\w+)', content)
            if default_match:
                exports.append(default_match.group(1))

        # Match named exports
        named_matches = re.findall(r'export\s+(?:const|let|var|function|class)\s+(\w+)', content)
        exports.extend(named_matches)

        return exports

    def _detect_styling_approach(self, content: str) -> str:
        """Detect styling approach"""
        if 'className=' in content and 'tailwind' in content.lower():
            return "tailwind"
        elif 'styled-components' in content or 'styled.' in content:
            return "styled-components"
        elif '@emotion' in content:
            return "emotion"
        elif 'className=' in content:
            return "css-modules"
        elif 'style={{' in content:
            return "inline-styles"
        else:
            return "unknown"

    def _detect_api_calls(self, content: str) -> List[str]:
        """Detect API calls and data fetching"""
        api_patterns = []

        if 'fetch(' in content:
            api_patterns.append("fetch")
        if 'axios' in content:
            api_patterns.append("axios")
        if 'useQuery' in content:
            api_patterns.append("react-query")
        if 'supabase' in content or 'from "@supabase' in content:
            api_patterns.append("supabase")

        return api_patterns

    def _detect_component_patterns(self, content: str) -> List[str]:
        """Detect common React patterns"""
        patterns = []

        # Check for common patterns
        if 'children' in content:
            patterns.append("composition")
        if 'render' in content and 'props.' in content:
            patterns.append("render-props")
        if re.search(r'with\w+\(', content):
            patterns.append("hoc")  # Higher-Order Component
        if 'Context.Provider' in content:
            patterns.append("context-provider")
        if 'useReducer' in content:
            patterns.append("reducer-pattern")

        return patterns

    def _analyze_project_structure(self) -> Dict:
        """Analyze project directory structure"""
        structure = {
            "src": {},
            "components": [],
            "pages": [],
            "hooks": [],
            "utils": [],
            "services": []
        }

        if not self.src_path.exists():
            return structure

        # Check for common directories
        common_dirs = ['components', 'pages', 'hooks', 'utils', 'services', 'api', 'lib']

        for dir_name in common_dirs:
            dir_path = self.src_path / dir_name
            if dir_path.exists():
                files = list(dir_path.rglob('*.{tsx,jsx,ts,js}'))
                structure[dir_name] = [str(f.relative_to(self.src_path)) for f in files]

        return structure

    def _identify_patterns(self) -> Dict:
        """Identify project-wide patterns"""
        patterns = {
            "lovable_conventions": self._check_lovable_conventions(),
            "common_hooks": self._find_common_hooks(),
            "component_hierarchy": self._build_component_hierarchy(),
            "styling_consistency": self._check_styling_consistency()
        }

        return patterns

    def _check_lovable_conventions(self) -> List[str]:
        """Check for Lovable-specific conventions"""
        conventions = []

        # Check if using Shadcn components
        if any('shadcn' in str(comp['imports']) for comp in self.components.values()):
            conventions.append("shadcn-ui")

        # Check if using Supabase
        if any('supabase' in str(comp['api_calls']) for comp in self.components.values()):
            conventions.append("supabase-integration")

        # Check if using Tailwind
        styling_approaches = [comp['styling'] for comp in self.components.values()]
        if styling_approaches.count('tailwind') > len(styling_approaches) * 0.5:
            conventions.append("tailwind-css")

        return conventions

    def _find_common_hooks(self) -> List[str]:
        """Find most commonly used hooks"""
        hook_usage = {}
        for component in self.components.values():
            for hook in component['hooks']:
                hook_usage[hook] = hook_usage.get(hook, 0) + 1

        # Return hooks used in >20% of components
        threshold = len(self.components) * 0.2
        common_hooks = [hook for hook, count in hook_usage.items() if count >= threshold]

        return common_hooks

    def _build_component_hierarchy(self) -> Dict:
        """Build component dependency hierarchy"""
        hierarchy = {}

        for comp_name, comp_info in self.components.items():
            # Find which components this one imports
            imported_components = []
            for imp in comp_info['imports']:
                # Check if import is another component
                if imp.startswith('.') or imp.startswith('@/'):
                    # Extract component name from path
                    comp_from_path = Path(imp).stem
                    if comp_from_path in self.components:
                        imported_components.append(comp_from_path)

            hierarchy[comp_name] = imported_components

        return hierarchy

    def _check_styling_consistency(self) -> str:
        """Check if styling is consistent across components"""
        styling_approaches = [comp['styling'] for comp in self.components.values()]

        if not styling_approaches:
            return "no-components"

        # Find most common approach
        most_common = max(set(styling_approaches), key=styling_approaches.count)
        consistency = styling_approaches.count(most_common) / len(styling_approaches)

        if consistency > 0.9:
            return f"consistent-{most_common}"
        elif consistency > 0.7:
            return f"mostly-{most_common}"
        else:
            return "mixed-approaches"

    def _calculate_stats(self) -> Dict:
        """Calculate project statistics"""
        return {
            "total_components": len(self.components),
            "functional_components": sum(1 for c in self.components.values() if c['type'].startswith('functional')),
            "class_components": sum(1 for c in self.components.values() if c['type'] == 'class'),
            "total_hooks": len(self.hooks),
            "components_with_state": sum(1 for c in self.components.values() if c['state']),
            "components_with_api_calls": sum(1 for c in self.components.values() if c['api_calls'])
        }

    def export_analysis(self, output_path: str):
        """Export analysis to JSON file"""
        analysis = self.analyze_project()

        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)

        print(f"[ReactAnalyzer] Analysis exported to: {output_path}")


# Example usage
if __name__ == "__main__":
    # Analyze a Lovable project
    project_path = "/Users/vik043/Desktop/Agentic Workflow/lovable-dashboard"

    if os.path.exists(project_path):
        analyzer = ReactAnalyzer(project_path)
        analysis = analyzer.analyze_project()

        print("\n=== React Project Analysis ===")
        print(f"Components: {analysis['stats']['total_components']}")
        print(f"Hooks: {analysis['stats']['total_hooks']}")
        print(f"Functional: {analysis['stats']['functional_components']}")
        print(f"Class: {analysis['stats']['class_components']}")

        print("\nCommon Hooks:")
        for hook in analysis['patterns']['common_hooks']:
            print(f"  - {hook}")

        print("\nLovable Conventions:")
        for convention in analysis['patterns']['lovable_conventions']:
            print(f"  ✓ {convention}")

        # Export to file
        output_path = "/Users/vik043/Desktop/Agentic Workflow/.tmp/react_analysis.json"
        analyzer.export_analysis(output_path)
    else:
        print(f"Project not found: {project_path}")
        print("Run Lovable sync first to clone the project")
