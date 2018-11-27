<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:fits="http://hul.harvard.edu/ois/xml/ns/fits/fits_output" exclude-result-prefixes="xs"
    version="2.0">
    <xsl:output method="text"/>
    <xsl:variable name="varTab">
        <xsl:text>&#x9;</xsl:text>
    </xsl:variable>

    <xsl:template match="fits:combined-fits">
        <xsl:text>format</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>filename</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>fileSize</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>checksum_md5</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>duration</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>sampleRate</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>bitDepth</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>pixelDimensions</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>resolution</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>bitsPerSample</xsl:text>
        <xsl:value-of select="$varTab"/>
        <xsl:text>colorSpace</xsl:text>
        <xsl:text>&#xa;</xsl:text>

        <xsl:for-each select="fits:fits">
            <xsl:choose>
                <xsl:when test="fits:identification/fits:identity/@format = 'Waveform Audio'">
                        <xsl:call-template name="WaveformAudio"/>
                </xsl:when>   
                <xsl:when test="fits:identification/fits:identity/@format = 'WAVE RF64'">
                    <xsl:call-template name="WaveformAudio"/>
                </xsl:when>
                <xsl:when test="fits:identification/fits:identity/@format = 'Portable Document Format'">
                    <xsl:call-template name="PDF"/>
                </xsl:when>
                <xsl:when test="fits:identification/fits:identity/@format = 'TIFF EXIF'">
                    <xsl:call-template name="TIFF"/>
                </xsl:when>
            </xsl:choose>
        </xsl:for-each>
    </xsl:template>



    <!-- Template for WAV audio files -->
    <xsl:template name="WaveformAudio">
        <xsl:value-of select="fits:identification/fits:identity[1]/@format"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:filename"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:size"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:md5checksum"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:metadata/fits:audio/fits:duration"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:metadata/fits:audio/fits:sampleRate"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:metadata/fits:audio/fits:bitDepth"/>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>
    
    <!-- Template for PDF files -->
    <xsl:template name="PDF">
        <xsl:value-of select="fits:identification/fits:identity[1]/@format"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:filename"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:size"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:md5checksum"/>
        <xsl:value-of select="$varTab"/>
        <xsl:text/>
        <xsl:value-of select="$varTab"/>
        <xsl:text/>
        <xsl:value-of select="$varTab"/>
        <xsl:text/>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>
    
    <!-- Template for TIFF files-->
    <xsl:template name="TIFF">
        <xsl:value-of select="fits:identification/fits:identity[1]/@format"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:filename"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:size"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:fileinfo/fits:md5checksum"/>
        <xsl:value-of select="$varTab"/>
        <xsl:text/>
        <xsl:value-of select="$varTab"/>
        <xsl:text/>
        <xsl:value-of select="$varTab"/>
        <xsl:text/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:metadata/fits:image/fits:imageWidth"/><xsl:text>x</xsl:text><xsl:value-of select="fits:metadata/fits:image/fits:imageHeight"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:metadata/fits:image/fits:xSamplingFrequency"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits/metadata/fits:image/fits:bitsPerSample/@toolname='Exiftool'"/>
        <xsl:value-of select="$varTab"/>
        <xsl:value-of select="fits:metadata/fits:image/fits:colorSpace"/>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>
</xsl:stylesheet>
