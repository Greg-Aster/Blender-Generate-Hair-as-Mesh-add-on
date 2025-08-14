# Mesh Hair Generator

A professional Blender addon for generating hair as actual mesh geometry, perfect for game development and GLB exports. Bypasses Blender's particle system limitations to create exportable hair with perfect material inheritance.

![Version](https://img.shields.io/badge/version-13.0-brightgreen)
![Blender](https://img.shields.io/badge/blender-4.4.3+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🌟 Features

### Core Functionality
- **Direct mesh generation** - No particle system conversion issues
- **Perfect material inheritance** - Hair matches surface textures exactly  
- **UV coordinate sampling** - Colors match underlying texture patterns
- **GLB export ready** - Single mesh object with proper materials
- **Batch processing** - Handle 100,000+ hair strands without crashes

### Render Types
- **🟢 Tubes** - Procedural hair geometry with customizable segments/sides
- **🔷 Object** - Use any custom mesh as hair (flowers, grass blades, etc.)

### Advanced Features
- **Progress tracking** - Real-time progress bar for large operations
- **Guide curves** - Direct hair flow with curve objects
- **Children system** - Thick, natural-looking hair clusters
- **Surface alignment** - Hair grows perpendicular to surface normals
- **Studio Ghibli styling** - Natural variation and organic appearance

## 📦 Installation

### Quick Install
1. Download `mesh_hair_generator_v13.zip`
2. In Blender: `Edit > Preferences > Add-ons > Install...`
3. Select the zip file and click "Install Add-on"
4. Enable "Mesh Hair Generator" in the addon list
5. Find the panel in `3D View > Sidebar > Mesh Hair` tab

### Manual Install
1. Extract the addon to your Blender addons folder:
   - **Windows:** `%APPDATA%/Blender Foundation/Blender/4.4/scripts/addons/`
   - **macOS:** `~/Library/Application Support/Blender/4.4/scripts/addons/`
   - **Linux:** `~/.config/blender/4.4/scripts/addons/`
2. Restart Blender and enable the addon

## 🚀 Quick Start

### Basic Hair Generation
1. **Select your mesh** (the surface to grow hair from)
2. **Open the Mesh Hair panel** (3D View sidebar)
3. **Set the emitter object** to your selected mesh
4. **Adjust hair count** (start with 1,000 for testing)
5. **Click "Generate Preview"**

### For Game Development
```
Recommended Settings:
- Hair Count: 5,000-20,000
- Render As: Tubes
- Segments: 1-2 (for performance)
- Sides: 3-4
- Use Batching: ✓ (for large counts)
- Keep Emitter Geometry: ✓
```

### For High-Quality Renders
```
Recommended Settings:
- Hair Count: 50,000+
- Render As: Tubes or Object
- Segments: 4-6
- Children Count: 3-5
- Use Surface Color: ✓
- Batch Size: 2,000-5,000
```

## 🎯 Use Cases

### Game Development
- **Grass fields** with perfect texture matching
- **Fur/hair** that exports to game engines
- **Vegetation** with custom object instancing
- **Environmental details** (moss, debris, etc.)

### Architectural Visualization
- **Landscape grass** matching terrain textures
- **Rooftop vegetation** with realistic distribution
- **Ground cover** with natural variation

### Animation & VFX
- **Character hair** with controllable flow
- **Environmental storytelling** through vegetation
- **Stylized effects** (Studio Ghibli style grass)

## ⚙️ Settings Reference

### Generation
| Setting | Description | Range | Default |
|---------|-------------|-------|---------|
| **Hair Count** | Number of hair strands | 1-100,000+ | 10,000 |
| **Hair Length** | Base length of strands | 0.01+ | 0.15 |
| **Length Random** | Random length variation | 0-1 | 0.3 |
| **Distribution** | How to spread hair | Random/Even/Density | Even |

### Render Type
| Setting | Description | Options |
|---------|-------------|---------|
| **Render As** | Hair geometry type | Tubes / Object |
| **Instance Object** | Custom mesh to use | Any mesh object |

### Tube Geometry
| Setting | Description | Range | Default |
|---------|-------------|-------|---------|
| **Segments** | Points along hair length | 1-20 | 6 |
| **Sides** | Tube cross-section sides | 2-8 | 4 |
| **Root Radius** | Thickness at base | 0.001+ | 0.005 |
| **Tip Radius** | Thickness at tip | 0+ | 0.001 |

### Object Settings
| Setting | Description | Range | Default |
|---------|-------------|-------|---------|
| **Scale** | Size multiplier | 0.01-10 | 1.0 |
| **Scale Random** | Random size variation | 0-1 | 0.3 |
| **Rotation Random** | Random rotation | 0-1 | 1.0 |
| **Align to Surface** | Follow surface normal | ✓/✗ | ✓ |

### Children System
| Setting | Description | Range | Default |
|---------|-------------|-------|---------|
| **Use Children** | Enable child hairs | ✓/✗ | ✓ |
| **Children Count** | Child hairs per parent | 0-10 | 3 |
| **Children Radius** | Spread around parent | 0.001-0.1 | 0.02 |
| **Children Length** | Length multiplier | 0.1-2 | 0.8 |

### Material & Color
| Setting | Description | Default |
|---------|-------------|---------|
| **Use Surface Color** | Sample emitter texture | ✓ |
| **Surface Color Blend** | Texture vs base color mix | 0.7 |
| **Base Color** | Fallback hair color | Green |
| **Color Random** | Random color variation | 0.1 |

### Performance
| Setting | Description | Range | Default |
|---------|-------------|-------|---------|
| **Use Preview** | Reduced hair for testing | ✓/✗ | ✓ |
| **Preview %** | Percentage of full count | 1-100 | 50 |
| **Use Batching** | Process in memory-safe chunks | ✓/✗ | ✓ |
| **Batch Size** | Strands per batch | 100-50,000 | 5,000 |

### Output Control
| Setting | Description | Default |
|---------|-------------|---------|
| **Keep Emitter Geometry** | Include original mesh | ✓ |
| **Shade Smooth** | Apply smooth shading to hair | ✓ |

## 🎨 Advanced Workflows

### Custom Object Hair
1. **Create your hair object** (grass blade, flower, etc.)
2. **Set Render As** to "Object"
3. **Select your object** in "Instance Object"
4. **Adjust scale and rotation** settings
5. **Generate hair** - each strand uses your custom object

### Guide Curve Control
1. **Create curve objects** to guide hair direction
2. **Add guide curves** in the addon panel
3. **Set influence** values for each guide
4. **Hair will follow** the curve directions

### Texture Color Matching
1. **Ensure your emitter has UV mapping** and materials
2. **Enable "Use Surface Color"**
3. **Adjust "Surface Color Blend"** to control texture influence
4. **Hair automatically samples** colors from the underlying texture

### Large-Scale Generation
1. **Enable "Use Batching"** for counts > 10,000
2. **Set appropriate batch size** based on your RAM
3. **Use fewer segments** (1-2) for better performance
4. **Monitor progress** in the console output

## 🔧 Performance Optimization

### Memory Management
- **Use batching** for large operations (>5,000 hairs)
- **Reduce segments** for simple geometry
- **Limit children count** for very dense hair
- **Close other applications** for maximum available RAM

### Speed Optimization
- **Start with preview mode** to test settings
- **Use lower hair counts** during development
- **Single segments** for ultra-fast generation
- **Disable children** for initial testing

### Batch Size Guidelines
| Hair Count | Recommended Batch Size | RAM Usage |
|------------|------------------------|-----------|
| 10,000 | 5,000 | Low |
| 50,000 | 3,000 | Medium |
| 100,000+ | 2,000 | High |

## 🐛 Troubleshooting

### Common Issues

**"No preview hair found"**
- Generate hair first, then try to finalize

**"Emitter has no active UV map"**
- Add UV mapping to your emitter object
- Unwrap the mesh in Edit mode

**Hair appears white/wrong colors**
- Check that emitter has materials with textures
- Ensure "Use Surface Color" is enabled
- Verify UV mapping is correct

**Blender becomes unresponsive**
- Reduce hair count or enable batching
- Lower batch size for your system's RAM
- Use fewer segments and children

**Hair grows in wrong direction**
- Check mesh normals (Edit mode > Mesh > Normals > Recalculate Outside)
- Ensure surface normals point outward

### Performance Issues
- **Enable batching** for large operations
- **Reduce hair count** for testing
- **Use preview mode** during development
- **Close other applications** to free RAM
- **Restart Blender** if memory becomes fragmented

## 📋 System Requirements

### Minimum
- **Blender:** 4.4.0+
- **RAM:** 4GB (for small operations)
- **Storage:** 10MB addon space

### Recommended
- **Blender:** 4.4.3+
- **RAM:** 16GB+ (for large operations)
- **CPU:** Multi-core for better performance
- **GPU:** Any (addon is CPU-based)

## 🤝 Contributing

This addon was developed for the MEGAMEAL project. Contributions and improvements are welcome!

### Development Setup
1. Clone/download the addon source
2. Make modifications to the Python files
3. Test in Blender development environment
4. Submit improvements via pull request

## 📄 License

MIT License - Feel free to use in commercial and personal projects.

## 🔗 Links

- **Documentation:** This README
- **Support:** GitHub Issues
- **Updates:** Check for new versions

## 📝 Changelog

### Version 13.0 🚀 **ARCHITECTURAL REVOLUTION**
- 🚀 **MASSIVE PERFORMANCE BOOST**: New "Separate Calculation from Creation" architecture
- ⚡ **10-100x faster hair generation** for tube-type hair through bulk processing
- 🎯 **Perfect color inheritance preserved** - identical results to v12 but orders of magnitude faster
- 💪 **Handles 50,000+ hairs effortlessly** without system instability or memory issues
- 🏗️ **Smart bulk processing**: Calculate ALL geometry data first, then build mesh in single operation
- 🔧 **Optimized parent-child system** - children preserve parent UV/material data exactly
- 📦 **Memory efficient**: Pre-allocated arrays and single bmesh update operations
- 🛠️ **Robust error handling**: Invalid faces skipped with detailed logging for debugging

### Version 10.0
- ✨ Minimum sides reduced to 2 (ultra-thin hair geometry)
- ✨ Shade smooth option for better visual quality
- 🎨 Enhanced hair appearance control

### Version 9.0
- ✨ Batch processing for large operations
- ✨ Single segment support (min segments = 1)
- 🚀 Performance optimizations
- 📊 Enhanced progress tracking

### Version 8.0
- 📊 Real-time progress bar
- 🔄 Responsive UI updates
- 🛡️ Error handling improvements

### Version 7.0
- 🎯 Object instancing support
- 🔷 Custom mesh hair rendering
- ⚙️ Advanced object controls

### Version 6.0
- 🎨 UV coordinate inheritance
- 🌈 Perfect texture color matching
- 🎯 Surface color sampling

### Version 5.0
- 🔄 Duplicate and prune workflow
- 🎯 Perfect material inheritance
- 🚀 Eliminated baking complexity

---

**Made with ❤️ for the Blender community**

*Transform your 3D scenes with professional hair generation that just works.*
