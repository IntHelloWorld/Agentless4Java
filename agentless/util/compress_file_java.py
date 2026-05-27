import tree_sitter_languages

parser = tree_sitter_languages.get_parser("java")

def process_node(node, raw_code, code_lines, chunks):
    if node.type == "method_declaration" or node.type == "constructor_declaration":
        node_start_line = node.start_point[0]
        body = node.child_by_field_name("body")
        if body:
            start_line = body.start_point[0]
            end_line = body.end_point[0]
            compressed_text = ""
            for i in range(node_start_line, start_line+1):
                if i == start_line:
                    compressed_text += code_lines[start_line][:body.start_point[1]]
                else:
                    compressed_text += code_lines[i] + "\n"
            chunks[node_start_line] = (f"{compressed_text}{{ ... }}\n", end_line+1)
            
    elif node.type == "class_declaration":
        for child in node.children:
            process_node(child, raw_code, code_lines, chunks)
            
    elif (node.type in ["field_declaration", "import_declaration", "package_declaration", "enum_declaration"]):
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        chunks[start_line] = ("", end_line+1)
    
    elif ("comment" in node.type):
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        chunks[start_line] = ("", end_line+1)

    else:
        for child in node.children:
            process_node(child, raw_code, code_lines, chunks)

def transform_code(code_lines, chunks):
    new_code = ""
    jump_to = -1
    for i, line in enumerate(code_lines):
        if i < jump_to:
            continue
        if i in chunks:
            text, end_line = chunks[i]
            new_code += text
            jump_to = end_line
        else:
            new_code += line + "\n"
    return new_code

def get_skeleton_java(
    raw_code,
    compress_assign: bool = False,
    total_lines=30,
    prefix_lines=10,
    suffix_lines=10,
):
    # try:
    tree = parser.parse(bytes(raw_code, "utf8"))
    root_node = tree.root_node
    
    code_lines = raw_code.split("\n")
    
    chunks = {}
    process_node(root_node, raw_code, code_lines, chunks)

    skeleton = transform_code(code_lines, chunks)
    return skeleton
        
    # except Exception as e:
    #     print(f"error: {e}")
    #     return raw_code

def test_java_compress():
    java_code = """
/**
 * An abstract base class that you can use to implement a new
 * {@link CategoryItemRenderer}.  When you create a new
 * {@link CategoryItemRenderer} you are not required to extend this class,
 * but it makes the job easier.
 */
public abstract class AbstractCategoryItemRenderer extends AbstractRenderer
        implements CategoryItemRenderer, Cloneable, PublicCloneable,
        Serializable {

    /** For serialization. */
    private static final long serialVersionUID = 1247553218442497391L;

    /** The plot that the renderer is assigned to. */
    private CategoryPlot plot;

    /** A list of item label generators (one per series). */
    private ObjectList itemLabelGeneratorList;

    /** The base item label generator. */
    private CategoryItemLabelGenerator baseItemLabelGenerator;

    /** A list of tool tip generators (one per series). */
    private ObjectList toolTipGeneratorList;

    /** The base tool tip generator. */
    private CategoryToolTipGenerator baseToolTipGenerator;

    /** A list of label generators (one per series). */
    private ObjectList urlGeneratorList;

    /** The base label generator. */
    private CategoryURLGenerator baseURLGenerator;

    /** The legend item label generator. */
    private CategorySeriesLabelGenerator legendItemLabelGenerator;

    /** The legend item tool tip generator. */
    private CategorySeriesLabelGenerator legendItemToolTipGenerator;

    /** The legend item URL generator. */
    private CategorySeriesLabelGenerator legendItemURLGenerator;

    /**
     * Annotations to be drawn in the background layer ('underneath' the data
     * items).
     *
     * @since 1.2.0
     */
    private List backgroundAnnotations;

    /**
     * Annotations to be drawn in the foreground layer ('on top' of the data
     * items).
     *
     * @since 1.2.0
     */
    private List foregroundAnnotations;

    /** The number of rows in the dataset (temporary record). */
    private transient int rowCount;

    /** The number of columns in the dataset (temporary record). */
    private transient int columnCount;

    /**
     * Creates a new renderer with no tool tip generator and no URL generator.
     * The defaults (no tool tip or URL generators) have been chosen to
     * minimise the processing required to generate a default chart.  If you
     * require tool tips or URLs, then you can easily add the required
     * generators.
     */
    protected AbstractCategoryItemRenderer() {
        this.itemLabelGeneratorList = new ObjectList();
        this.toolTipGeneratorList = new ObjectList();
        this.urlGeneratorList = new ObjectList();
        this.legendItemLabelGenerator
                = new StandardCategorySeriesLabelGenerator();
        this.backgroundAnnotations = new ArrayList();
        this.foregroundAnnotations = new ArrayList();
    }

    /**
     * Returns the number of passes through the dataset required by the
     * renderer.  This method returns <code>1</code>, subclasses should
     * override if they need more passes.
     *
     * @return The pass count.
     */
    public int getPassCount() {
        return 1;
    }

    /**
     * Returns the plot that the renderer has been assigned to (where
     * <code>null</code> indicates that the renderer is not currently assigned
     * to a plot).
     *
     * @return The plot (possibly <code>null</code>).
     *
     * @see #setPlot(CategoryPlot)
     */
    public CategoryPlot getPlot() {
        return this.plot;
    }

    /**
     * Sets the plot that the renderer has been assigned to.  This method is
     * usually called by the {@link CategoryPlot}, in normal usage you
     * shouldn't need to call this method directly.
     *
     * @param plot  the plot (<code>null</code> not permitted).
     *
     * @see #getPlot()
     */
    public void setPlot(CategoryPlot plot) {
        if (plot == null) {
            throw new IllegalArgumentException("Null 'plot' argument.");
        }
        this.plot = plot;
    }

    // ITEM LABEL GENERATOR

    /**
     * Returns the item label generator for a data item.  This implementation
     * returns the series item label generator if one is defined, otherwise
     * it returns the default item label generator (which may be
     * <code>null</code>).
     *
     * @param row  the row index (zero based).
     * @param column  the column index (zero based).
     * @param selected  is the item selected?
     *
     * @return The generator (possibly <code>null</code>).
     *
     * @since 1.2.0
     */
    public CategoryItemLabelGenerator getItemLabelGenerator(int row,
            int column, boolean selected) {
        CategoryItemLabelGenerator generator = (CategoryItemLabelGenerator)
                this.itemLabelGeneratorList.get(row);
        if (generator == null) {
            generator = this.baseItemLabelGenerator;
        }
        return generator;
    }

    /**
     * Returns the item label generator for a series.
     *
     * @param series  the series index (zero based).
     *
     * @return The generator (possibly <code>null</code>).
     *
     * @see #setSeriesItemLabelGenerator(int, CategoryItemLabelGenerator)
     */
    public CategoryItemLabelGenerator getSeriesItemLabelGenerator(int series) {
        return (CategoryItemLabelGenerator) this.itemLabelGeneratorList.get(
                series);
    }

    /**
     * Sets the item label generator for a series and sends a
     * {@link RendererChangeEvent} to all registered listeners.
     *
     * @param series  the series index (zero based).
     * @param generator  the generator (<code>null</code> permitted).
     *
     * @see #getSeriesItemLabelGenerator(int)
     */
    public void setSeriesItemLabelGenerator(int series,
            CategoryItemLabelGenerator generator) {
        setSeriesItemLabelGenerator(series, generator, true);
    }

    /**
     * Sets the item label generator for a series and, if requested, sends a
     * {@link RendererChangeEvent} to all registered listeners.
     *
     * @param series  the series index (zero based).
     * @param generator  the generator (<code>null</code> permitted).
     * @param notify  notify listeners?
     *
     * @since 1.2.0
     *
     * @see #getSeriesItemLabelGenerator(int)
     */
    public void setSeriesItemLabelGenerator(int series,
            CategoryItemLabelGenerator generator, boolean notify) {
        this.itemLabelGeneratorList.set(series, generator);
        if (notify) {
            notifyListeners(new RendererChangeEvent(this));
        }
    }

    /**
     * Returns the base item label generator.
     *
     * @return The generator (possibly <code>null</code>).
     *
     * @see #setBaseItemLabelGenerator(CategoryItemLabelGenerator)
     */
    public CategoryItemLabelGenerator getBaseItemLabelGenerator() {
        return this.baseItemLabelGenerator;
    }

    /**
     * Sets the base item label generator and sends a
     * {@link RendererChangeEvent} to all registered listeners.
     *
     * @param generator  the generator (<code>null</code> permitted).
     *
     * @see #getBaseItemLabelGenerator()
     */
    public void setBaseItemLabelGenerator(
            CategoryItemLabelGenerator generator) {
        setBaseItemLabelGenerator(generator, true);
    }

    /**
     * Sets the base item label generator and, if requested, sends a
     * {@link RendererChangeEvent} to all registered listeners.
     *
     * @param generator  the generator (<code>null</code> permitted).
     * @param notify  notify listeners?
     *
     * @since 1.2.0
     *
     * @see #getBaseItemLabelGenerator()
     */
    public void setBaseItemLabelGenerator(
            CategoryItemLabelGenerator generator, boolean notify) {
        this.baseItemLabelGenerator = generator;
        if (notify) {
            notifyListeners(new RendererChangeEvent(this));
        }
    }
    
}

"""
    
    skeleton = get_skeleton_java(java_code)
    print(skeleton)

if __name__ == "__main__":
    test_java_compress()
